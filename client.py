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

# Close the socket after the connection test is complete
client_socket.close()