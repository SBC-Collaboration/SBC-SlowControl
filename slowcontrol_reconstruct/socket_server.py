import socket
import json
import SBC_env as env

# Server configuration
HOST = '127.0.0.1'
PORT = 12345

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()

print(f"Server listening on {HOST}:{PORT}")

while True:
    # Accept a connection from a client
    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")

    # Receive data from the client
    received_data = client_socket.recv(1024).decode('utf-8')

    # Deserialize the received JSON data into a dictionary
    received_dict = json.loads(received_data)
    print("Received data from client:", received_dict)

    # Create a response dictionary
    response_dict = env.DIC_PACK
    # response_dict ={'message': 'Hello from server!', 'status': 'OK'}

    # Serialize the response dictionary into JSON
    response_data = json.dumps(response_dict).encode('utf-8')

    # Send the response data back to the client
    client_socket.send(response_data)

    # Close the connection with the client
    client_socket.close()