import socket
import os
import re
import sys
from urllib.parse import urlparse, urljoin

# Get the server host and port from command-line arguments, defaulting to localhost:8080
HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8080


# Fetch a resource using the same HTTP client logic
def fetch_resource(request_path):

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
        f"GET {request_path} HTTP/1.0\r\n"
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
        
    # Handle a malformed response without crashing
    if b"\r\n\r\n" not in response_data:
        print("Error: Malformed HTTP response")
        client_socket.close()
        return []

    # Separate the HTTP headers from the response body
    header_data, body = response_data.split(b"\r\n\r\n", 1)

    # Decode the headers so Content-Length can be read
    header_text = header_data.decode("ascii", errors="ignore")

    # Parse the HTTP status line
    header_lines = header_text.split("\r\n")
    status_line = header_lines[0]
    
    status_parts = status_line.split(" ", 2)

    if len(status_parts) != 3:
        print("Error: Malformed HTTP status line")
        client_socket.close()
        return []

    http_version, status_code, reason_phrase = status_parts
    try:
        status_code = int(status_code)
    except ValueError:
        print("Error: Malformed HTTP status code")
        client_socket.close()
        return []

    # Parse all HTTP headers into a structured dictionary
    headers = {}

    for line in header_lines[1:]:
        if ":" in line:
            header_name, header_value = line.split(":", 1)
            headers[header_name.strip().lower()] = header_value.strip()

    content_length = None

    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            try:
                content_length = int(line.split(":", 1)[1].strip())
            except ValueError:
                print("Error: Malformed Content-Length header")
                client_socket.close()
                return []
            break
        
    if content_length is None:
        print("Error: Missing Content-Length header")
        client_socket.close()
        return []
    
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
        
    # Handle an incomplete response body without crashing
    if len(body) != content_length:
        print("Error: Incomplete HTTP response body")
        client_socket.close()
        return []
            
    # Handle HTTP status codes
    embedded_resources = []
    
    if status_code == 200:
        print(f"Success: {status_code} {reason_phrase}")
        
        # Save every successfully fetched resource to a local output directory
        os.makedirs("output", exist_ok=True)

        filename = os.path.basename(request_path)

        if not filename:
            filename = "index.html"

        output_path = os.path.join("output", filename)

        with open(output_path, "wb") as file:
            file.write(body)

        print(f"Saved: {output_path}")
        
        # Scan HTML for embedded <img src> and <link href> resources
        if headers.get("content-type", "").startswith("text/html"):
            html_text = body.decode("utf-8", errors="ignore")

            img_sources = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_text)
            link_sources = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html_text)

            for resource in img_sources + link_sources:
                parsed_resource = urlparse(resource)

                # Fetch only resources that point to the same host and port
                if parsed_resource.hostname:
                    resource_port = parsed_resource.port or 80

                    if parsed_resource.hostname != HOST or resource_port != PORT:
                        continue

                resource_path = urljoin(request_path, resource)
                parsed_path = urlparse(resource_path).path

                embedded_resources.append(parsed_path)
                
            print(f"Embedded resources: {embedded_resources}")
            

    elif status_code in (301, 302):
        location = headers.get("location", "Location header not found")
        print(f"Redirect: {status_code} {reason_phrase} -> {location}")

    elif 400 <= status_code <= 599:
        print(f"Error: {status_code} {reason_phrase}")

    # Close the socket after the request-response exchange is complete
    client_socket.close()
    return embedded_resources
    

embedded_resources = fetch_resource("/pages/index.html")

for resource in embedded_resources:
    fetch_resource(resource)