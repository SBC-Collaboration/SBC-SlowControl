import socket
import json

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 5555

    while True:
        try:
            client_socket.connect((host, port))

            # Set a timeout for socket operations to 10 seconds
            client_socket.settimeout(10)

            while True:
                # Receive JSON data from the server
                json_data = client_socket.recv(1024).decode('utf-8')

                # Deserialize JSON data to a dictionary
                data_dict = json.loads(json_data)

                print(f"Received from server: {data_dict}")

        except socket.timeout:
            print("Connection timed out. Restarting client...")
            client_socket.close()
            start_client()
        except Exception as e:
            print("Connection broken. Restarting server...")
            client_socket.close()
            start_client()

if __name__ == "__main__":
    start_client()
