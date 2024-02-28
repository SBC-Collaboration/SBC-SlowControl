import socket
import json
import time

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '127.0.0.1'
    port = 5555
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Server listening on {host}:{port}")

    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")

            # Set a timeout for socket operations to 10 seconds
            conn.settimeout(10)

            while True:
                # Create a sample dictionary
                data_dict = {'key': 'value', 'number': 42}

                # Serialize the dictionary to JSON
                json_data = json.dumps(data_dict)

                # Send JSON data to the client
                conn.send(json_data.encode('utf-8'))

                time.sleep(5)  # Sleep for 5 seconds before sending data again

        except socket.timeout:
            print("Connection timed out. Restarting server...")
            conn.close()
            server_socket.close()
            start_server()
        except Exception as e:
            print("Connection broken. Restarting server...")
            conn.close()
            server_socket.close()
            start_server()

if __name__ == "__main__":
    start_server()