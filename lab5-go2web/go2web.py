import sys
import socket
import ssl
from html.parser import HTMLParser
from urllib.parse import urlparse


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
  go2web -u <URL>         Make an HTTP request to the specified URL
  go2web -s <search-term> Search the term using a search engine
  go2web -h               Show this help
""")


def extract_readable_text(html: str) -> str:
  parser = TextExtractor()
  parser.feed(html)
  return parser.get_text()


def make_http_request(url: str):
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
    f"Connection: close\r\n"
    f"\r\n"
  )

  try:
    with socket.create_connection((host, port), timeout=10) as sock:
      if parsed.scheme == "https":
        context = ssl.create_default_context()
        with context.wrap_socket(sock, server_hostname=host) as secure_sock:
          secure_sock.sendall(request.encode("utf-8"))

          response_chunks = []
          while True:
            chunk = secure_sock.recv(4096)
            if not chunk:
              break
            response_chunks.append(chunk)
      else:
        sock.sendall(request.encode("utf-8"))

        response_chunks = []
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

  return status_line, headers, body


def fetch_url(url: str, max_redirects: int = 5):
  current_url = url

  for _ in range(max_redirects + 1):
    status_line, headers, body = make_http_request(current_url)

    if status_line is None:
      return

    print("=== RESPONSE STATUS ===")
    print(status_line)

    if status_line.startswith("HTTP/1.1 301") or \
      status_line.startswith("HTTP/1.1 302") or \
      status_line.startswith("HTTP/1.1 307") or \
      status_line.startswith("HTTP/1.1 308"):
      location = headers.get("location")
      if location:
        print(f"Redirect detected -> {location}\n")
        current_url = location
        continue

    content_type = headers.get("content-type", "")

    print("\n=== RESPONSE HEADERS ===")
    for key, value in headers.items():
      print(f"{key}: {value}")

    print("\n=== RESPONSE BODY ===")
    if "text/html" in content_type:
      readable = extract_readable_text(body)
      print(readable[:3000])
    else:
      print(body[:3000])
    return

  print("Error: too many redirects")


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
    print("Searching:", term)

  else:
    print("Unknown command")
    show_help()


if __name__ == "__main__":
  main()
