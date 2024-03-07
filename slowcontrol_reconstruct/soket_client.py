import socket
import json

# Client configuration
HOST = '127.0.0.1'
PORT = 12345

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((HOST, PORT))

# Create a dictionary to send to the server
data_to_send = {'key': 'value', 'number': 42}

# Serialize the dictionary into JSON
serialized_data = json.dumps(data_to_send).encode('utf-8')

# Send the serialized data to the server
client_socket.send(serialized_data)

# Receive data from the server
received_data = client_socket.recv(1024).decode('utf-8')

# Deserialize the received JSON data into a dictionary
received_dict = json.loads(received_data)
print("Received data from server:", received_dict)

# Close the connection with the server
client_socket.close()
