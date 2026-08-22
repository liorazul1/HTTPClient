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

# Close the socket after the connection test is complete
client_socket.close()