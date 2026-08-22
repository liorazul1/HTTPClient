import socket

# The IP address of the server
HOST = "127.0.0.1"

# The port on which our HTTP server is listening
PORT = 8080

# Create a TCP socket using IPv4
client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

# Establish a TCP connection with the server
client_socket.connect((HOST, PORT))

print(f"Connected to {HOST}:{PORT}")

# Build a valid HTTP/1.0 GET request manually as raw text.
request = (
    "GET /pages/index.html HTTP/1.0\r\n"
    f"Host: {HOST}\r\n"
    "\r\n"
)

# Send the HTTP/1.0 GET request over the socket
client_socket.sendall(request.encode("ascii"))

# Buffer incoming bytes dynamically until the HTTP header terminator is found
response_data = b""

while b"\r\n\r\n" not in response_data:

    # Read from the socket without assuming the headers arrive in one recv() call
    chunk = client_socket.recv(4096)

    # Stop if the server closes the connection
    if not chunk:
        break

    response_data += chunk

# Separate the HTTP headers from the response body
header_data, body = response_data.split(b"\r\n\r\n", 1)

# Decode the headers so Content-Length can be read
header_text = header_data.decode("ascii", errors="ignore")

# Parse the HTTP status line
header_lines = header_text.split("\r\n")
status_line = header_lines[0]

http_version, status_code, reason_phrase = status_line.split(" ", 2)
status_code = int(status_code)

# Parse all HTTP headers into a structured dictionary
headers = {}

for line in header_lines[1:]:
    if ":" in line:
        header_name, header_value = line.split(":", 1)
        headers[header_name.strip().lower()] = header_value.strip()

content_length = 0

for line in header_text.split("\r\n"):
    if line.lower().startswith("content-length:"):
        content_length = int(line.split(":", 1)[1].strip())
        break

# Read exactly Content-Length bytes for the body
while len(body) < content_length:

    # Handle partial reads across multiple recv() calls
    chunk = client_socket.recv(
        min(4096, content_length - len(body))
    )

    # Stop if the server closes the connection
    if not chunk:
        break

    body += chunk
    
# Handle HTTP status codes
if status_code == 200:
    print(f"Success: {status_code} {reason_phrase}")

elif status_code in (301, 302):
    location = headers.get("location", "Location header not found")
    print(f"Redirect: {status_code} {reason_phrase} -> {location}")

elif 400 <= status_code <= 599:
    print(f"Error: {status_code} {reason_phrase}")

# Close the socket after the connection test is complete
client_socket.close()