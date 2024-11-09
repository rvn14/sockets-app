import socket
import threading
import os
import time


PORT = 5001
BUFF_SIZE = 8192
FILE_DIR = "./files"

def format_size(size_in_bytes):
    # Convert the file size into a readable format
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
        
def compare_file_size(file_path, expected_size):
    actual_size = os.path.getsize(file_path)
    
    if actual_size == expected_size:
        print(f"File size matches: {format_size(int(actual_size))} bytes")
    else:
        print(f"File size mismatch: expected {format_size(int(expected_size))} bytes, got {format_size(int(actual_size))} bytes")

def handle_client_req(client_socket):
    try:
        request = client_socket.recv(BUFF_SIZE).decode("utf-8")
        print(f"Received request: {request}")
        
        if request.startswith("GET") or request.startswith("SEND"):
            command, file_name = request.split(" ")
            file_path = os.path.join(FILE_DIR, file_name)   
        else:
            command = request
            
        if command == "LIST":
            # Send list of files in the directory
            try:
                files = os.listdir(FILE_DIR)
                if not files:
                    client_socket.sendall(b"No files available on the server.")
                    return
        
                formatted_list = "Filename\t\tSize\t\tLast Modified\n"
                formatted_list += "=" * 50 + "\n"
        
                for file_name in files:
                    file_path = os.path.join(FILE_DIR, file_name)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        last_modified = time.ctime(os.path.getmtime(file_path))
                        formatted_list += f"{file_name:20}\t{size/1024:.2f} KB\t{last_modified}\n"
        
                client_socket.sendall(formatted_list.encode("utf-8"))
            except Exception as e:
                print(f"Error listing files: {e}")
                client_socket.sendall(b"ERROR: Could not retrieve file list.")    
        
        elif command.upper() == "GET":
            # Send the file data in chunks
            try:
                
                actual_size = str(os.path.getsize(file_path))
                client_socket.sendall((actual_size).encode("utf-8"))
                
                client_socket.recv(BUFF_SIZE) 
                
                client_socket.sendall(b"READY")
                
                client_socket.recv(BUFF_SIZE) 
                
                with open(file_path, "rb") as file:
                    
                    while (data := file.read(BUFF_SIZE)):
                        client_socket.sendall(data)
                print(f"File {file_name} sent successfully.")        
                        
            except FileNotFoundError:
                print(f"File {file_name} not found")
                client_socket.sendall(b"ERROR")
        
        elif command.upper() == "SEND":
            client_socket.sendall(b"READY")
            
            try:
                expected_size = client_socket.recv(BUFF_SIZE).decode("utf-8")
                print(f"Expected size: {format_size(int(expected_size))}")

                client_socket.sendall(b"SIZE_RECEIVED")
            except:
                print("Error receiving file size")
                return
            
            # Receive and write the file data in chunks
            status = client_socket.recv(BUFF_SIZE).decode("utf-8")
            print(f"Received status: {status}")
            try:
                if status == "OK":
                    with open(file_path, "wb") as file:
                        while True:
                            data = client_socket.recv(BUFF_SIZE)
                            if not data:
                                break
                            file.write(data)
                    print(f"File {file_name} downloaded successfully.")
                    compare_file_size(os.path.join(FILE_DIR, file_name), int(expected_size))
                else:
                    print(f"Error receiving file {file_name}")
            except Exception as e:
                print(f"An error occurred")
        
        elif command.upper() == "DISCONNECT":
            print("Client disconnected")
            os._exit(0)


        
        else:
            print("Invalid command")
            client_socket.sendall(b"ERROR: Invalid command.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        client_socket.close()

def main():
    host = socket.gethostbyname(socket.gethostname())
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, PORT))
    server_socket.listen(5)
    
    print(f"Server listening on {host}:{PORT}")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        
        client_handler = threading.Thread(target=handle_client_req, args=(client_socket,))
        client_handler.start()
        
    server_socket.close()

if __name__ == "__main__":
    main()
