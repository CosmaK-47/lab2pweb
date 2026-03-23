# Lab 5 – HTTP over TCP Sockets

## 📌 Description

This project implements a command-line tool called `go2web` that performs HTTP requests directly over TCP sockets without using any built-in or third-party HTTP libraries.

The tool can:
- Fetch and display web pages
- Perform search queries and display top results
- Handle both HTML and JSON responses
- Follow HTTP redirects
- Cache responses for improved performance

---

## ⚙️ Features

### 🔹 CLI Commands
 - go2web -u <URL> Make an HTTP request to the specified URL
 - go2web -s <search-term> Search the term using a search engine and print top 10 results
 - go2web -h Show help


---

### 🌐 HTTP Client Implementation

- Built using:
  - `socket` (TCP communication)
  - `ssl` (HTTPS support)
- Supports:
  - HTTP and HTTPS
  - Manual request construction
  - Response parsing

---

### 🔁 Redirect Handling

Supports HTTP status codes:
- 301
- 302
- 303
- 307
- 308

Automatically follows redirects until a final response is received.

---

### 📦 Chunked Transfer Decoding

Handles responses with:
- `Transfer-Encoding: chunked`

Decodes the response body manually according to the HTTP specification.

---

### 🧠 Content Processing

- HTML → converted to human-readable text (HTML tags removed)
- JSON → pretty printed using formatted output

---

### 🔍 Search Functionality

Uses Wikipedia API:
- Endpoint: `https://en.wikipedia.org/w/api.php`

Returns:
- Top 10 results
- Title + URL for each result

---

### 💾 Cache Mechanism

- Stores responses locally in `.cache/`
- Uses SHA-256 hashing for unique filenames
- Cache expiration: 5 minutes
- Improves performance by avoiding repeated network calls

---

## 🖥️ Example Usage

### Help
go2web -h

---

### Fetch URL
go2web -u https://www.example.com
go2web -u https://httpbin.org/json


---

### Search
go2web -s coffee
go2web -s tcp protocol


---

## ▶️ How to Run

### Windows

Make sure Python is installed, then run:
 - go2web -h


---

## 🎯 Bonus Features Implemented

- ✅ HTTP redirects handling
- ✅ HTTP cache mechanism
- ✅ JSON and HTML content processing
- ✅ HTTPS support via SSL

---

## 🧪 Technologies Used

- Python 3
- TCP sockets
- SSL/TLS
- HTML parsing (HTMLParser)
- JSON processing

---

## 📸 Demo

Add a GIF here showing:
go2web -h
go2web -u http://example.com

go2web -u https://httpbin.org/json

go2web -s coffee
