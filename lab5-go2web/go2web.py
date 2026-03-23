import sys
import os
import time
import json
import socket
import ssl
import hashlib
from html.parser import HTMLParser
from urllib.parse import urlparse, quote_plus, urljoin


CACHE_DIR = ".cache"
CACHE_TTL_SECONDS = 300


class TextExtractor(HTMLParser):
  def __init__(self):
    super().__init__()
    self.parts = []
    self.ignore_tag = None

  def handle_starttag(self, tag, attrs):
    if tag in ("script", "style"):
      self.ignore_tag = tag

  def handle_endtag(self, tag):
    if tag == self.ignore_tag:
      self.ignore_tag = None

  def handle_data(self, data):
    if self.ignore_tag is not None:
      return

    text = data.strip()
    if text:
      self.parts.append(text)

  def get_text(self):
    return "\n".join(self.parts)


def show_help():
  print("""
Usage:
  go2web -u <URL>         Make an HTTP request to the specified URL and print the response
  go2web -s <search-term> Search the term using a search engine and print top 10 results
  go2web -h               Show this help
""")


def extract_readable_text(html: str) -> str:
  parser = TextExtractor()
  parser.feed(html)
  return parser.get_text()


def decode_chunked_body(body: str) -> str:
  decoded = ""
  i = 0

  while i < len(body):
    line_end = body.find("\r\n", i)
    if line_end == -1:
      break

    chunk_size_line = body[i:line_end].strip()

    try:
      chunk_size = int(chunk_size_line, 16)
    except ValueError:
      break

    if chunk_size == 0:
      break

    i = line_end + 2
    chunk_data = body[i:i + chunk_size]
    decoded += chunk_data
    i += chunk_size + 2

  return decoded


def normalize_body(headers: dict, body: str) -> str:
  if headers.get("transfer-encoding", "").lower() == "chunked":
    body = decode_chunked_body(body)
  return body


def get_cache_path(url: str) -> str:
  os.makedirs(CACHE_DIR, exist_ok=True)
  filename = hashlib.sha256(url.encode("utf-8")).hexdigest() + ".txt"
  return os.path.join(CACHE_DIR, filename)


def load_from_cache(url: str):
  cache_path = get_cache_path(url)

  if not os.path.exists(cache_path):
    return None

  age = time.time() - os.path.getmtime(cache_path)
  if age > CACHE_TTL_SECONDS:
    return None

  try:
    with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
      cached = f.read()
  except OSError:
    return None

  parts = cached.split("\n\n", 1)
  if len(parts) != 2:
    return None

  headers_block, body = parts
  lines = headers_block.splitlines()
  if not lines:
    return None

  status_line = lines[0]
  headers = {}

  for line in lines[1:]:
    if ": " in line:
      key, value = line.split(": ", 1)
      headers[key.lower()] = value

  return status_line, headers, body


def save_to_cache(url: str, status_line: str, headers: dict, body: str):
  cache_path = get_cache_path(url)

  lines = [status_line]
  for key, value in headers.items():
    lines.append(f"{key}: {value}")

  try:
    with open(cache_path, "w", encoding="utf-8") as f:
      f.write("\n".join(lines))
      f.write("\n\n")
      f.write(body)
  except OSError:
    pass


def make_http_request(url: str, use_cache: bool = True):
  if use_cache:
    cached_response = load_from_cache(url)
    if cached_response is not None:
      return cached_response

  parsed = urlparse(url)

  if parsed.scheme not in ("http", "https"):
    print("Error: only http:// and https:// are supported")
    return None, None, None

  host = parsed.hostname
  port = parsed.port or (443 if parsed.scheme == "https" else 80)
  path = parsed.path if parsed.path else "/"

  if parsed.query:
    path += "?" + parsed.query

  request = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    f"User-Agent: go2web/1.0\r\n"
    f"Accept: text/html,application/json\r\n"
    f"Accept-Language: en-US,en;q=0.9\r\n"
    f"Connection: close\r\n"
    f"\r\n"
  )

  response_chunks = []

  try:
    with socket.create_connection((host, port), timeout=10) as sock:
      if parsed.scheme == "https":
        context = ssl.create_default_context()
        with context.wrap_socket(sock, server_hostname=host) as secure_sock:
          secure_sock.sendall(request.encode("utf-8"))

          while True:
            chunk = secure_sock.recv(4096)
            if not chunk:
              break
            response_chunks.append(chunk)
      else:
        sock.sendall(request.encode("utf-8"))

        while True:
          chunk = sock.recv(4096)
          if not chunk:
            break
          response_chunks.append(chunk)

  except Exception as e:
    print(f"Connection error: {e}")
    return None, None, None

  response = b"".join(response_chunks).decode("utf-8", errors="replace")

  parts = response.split("\r\n\r\n", 1)
  if len(parts) == 2:
    headers_text, body = parts
  else:
    headers_text, body = response, ""

  header_lines = headers_text.split("\r\n")
  status_line = header_lines[0] if header_lines else ""
  headers = {}

  for line in header_lines[1:]:
    if ": " in line:
      key, value = line.split(": ", 1)
      headers[key.lower()] = value

  if use_cache:
    save_to_cache(url, status_line, headers, body)

  return status_line, headers, body


def print_response_body(headers: dict, body: str):
  content_type = headers.get("content-type", "")
  print("\n=== RESPONSE BODY ===")

  if "application/json" in content_type:
    try:
      parsed_json = json.loads(body)
      print(json.dumps(parsed_json, indent=2, ensure_ascii=False)[:3000])
    except json.JSONDecodeError:
      print(body[:3000])

  elif "text/html" in content_type:
    readable = extract_readable_text(body)
    print(readable[:3000])

  else:
    print(body[:3000])


def fetch_url(url: str, max_redirects: int = 5):
  current_url = url

  for _ in range(max_redirects + 1):
    status_line, headers, body = make_http_request(current_url, use_cache=True)

    if status_line is None:
      return

    print("=== RESPONSE STATUS ===")
    print(status_line)

    try:
      status_code = int(status_line.split()[1])
    except (IndexError, ValueError):
      print("Error: invalid HTTP status line")
      return

    if status_code in (301, 302, 303, 307, 308):
      location = headers.get("location")
      if location:
        next_url = urljoin(current_url, location)
        print(f"Redirect detected -> {next_url}\n")
        current_url = next_url
        continue

    body = normalize_body(headers, body)

    print("\n=== RESPONSE HEADERS ===")
    for key, value in headers.items():
      print(f"{key}: {value}")

    print_response_body(headers, body)
    return

  print("Error: too many redirects")


def search_web(term: str):
  query = quote_plus(term)

  search_url = (
    "https://en.wikipedia.org/w/api.php"
    f"?action=query&list=search&srsearch={query}&format=json&srlimit=10"
  )

  status_line, headers, body = make_http_request(search_url, use_cache=False)

  if status_line is None or body is None:
    print("Search request failed: no usable response received")
    return

  try:
    status_code = int(status_line.split()[1])
  except (IndexError, ValueError):
    print("Search request failed: invalid HTTP status line")
    return

  if status_code != 200:
    print("Search request failed:")
    print(status_line)
    return

  body = normalize_body(headers, body)

  try:
    parsed = json.loads(body)
  except json.JSONDecodeError:
    print("Search request failed: invalid JSON response")
    return

  results = parsed.get("query", {}).get("search", [])

  print(f"\nTop results for: {term}\n")

  if not results:
    print("No results found.")
    return

  for index, item in enumerate(results[:10], 1):
    title = item.get("title", "Untitled")
    url_title = title.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{url_title}"

    print(f"{index}. {title}")
    print(f"   {url}\n")


def main():
  args = sys.argv

  if len(args) < 2:
    show_help()
    return

  if args[1] == "-h":
    show_help()

  elif args[1] == "-u":
    if len(args) < 3:
      print("Error: URL missing")
      return

    fetch_url(args[2])

  elif args[1] == "-s":
    if len(args) < 3:
      print("Error: search term missing")
      return

    term = " ".join(args[2:])
    search_web(term)

  else:
    print("Unknown command")
    show_help()


if __name__ == "__main__":
  main()
