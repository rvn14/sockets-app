import socket
import os
from tkinter import filedialog
import time


# host = "localhost"
PORT = 5001
BUFF_SIZE = 8192
DOWN_DIR = "./downloads"

def browse_files(self):
        """Open file browser dialog and return selected file path"""
        file_path = filedialog.askopenfilename(
            title='Select a file to upload',
            initialdir=os.path.expanduser("~"),  # Start from home directory
            filetypes=[('All Files', '*.*')]
        )
        return file_path
    
    
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

def list_files(dir_name,host):
    if dir_name.lower() == "server":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, PORT))
            
            # Send LIST command
            client_socket.sendall(b"LIST")
            
            # Receive and print the list of files
            file_list = client_socket.recv(BUFF_SIZE).decode("utf-8")
            if file_list.startswith("ERROR"):
                print("Error listing files")
            else:
                print("\nAvailable files:\n\n", file_list)
            
    elif dir_name.lower() == "client":
        files = os.listdir(DOWN_DIR)
        if not files:
            print("No files available in the client directory.")
            return
        
        print("Available files in client directory:")
        for file_name in files:
            file_path = os.path.join(DOWN_DIR, file_name)
            size = os.path.getsize(file_path) / 1024  # Convert bytes to KB
            last_modified = time.ctime(os.path.getmtime(file_path))
            print(f"{file_name:20}\t{size:.2f} KB\t{last_modified}")


def get_file(file_name, host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, PORT))
        
        # Request file and receive expected size
        client_socket.sendall(f"GET {file_name}".encode("utf-8"))
        
        # Receive expected file size
        try:
            expected_size = int(client_socket.recv(BUFF_SIZE).decode("utf-8"))
            print(f"Expected size: {format_size(expected_size)}")
        
        # Acknowledge size receipt
            client_socket.sendall(b"SIZE_RECEIVED")
        except:
            print("File not found")
            return
        
        # Check server response status
        status = client_socket.recv(BUFF_SIZE).decode("utf-8")
        print(f"Received status: {status}")
        
        client_socket.sendall(b"READY")
        
        if status == "ERROR":
            print(f"File {file_name} not found")
            return
        elif status == "READY":
            # Open the file in binary mode to write incoming data
            file_path = os.path.join(DOWN_DIR, file_name)
            with open(file_path, "wb") as file:
                received_size = 0
                while True:
                    data = client_socket.recv(BUFF_SIZE)
                    if not data:
                        break
                    file.write(data)
                    received_size += len(data)
            
            # Validate received file size
            if received_size == expected_size:
                print(f"File {file_name} downloaded successfully.")
            else:
                print(f"File {file_name} downloaded partially. Expected {expected_size} bytes, got {received_size} bytes.")

def send_file(file_name, host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, PORT))
        client_socket.sendall(f"SEND {file_name}".encode("utf-8"))
        
        status = client_socket.recv(BUFF_SIZE).decode("utf-8")
        if status == "READY": 
            try:
                with open(os.path.join(DOWN_DIR, file_name), "rb") as file:
                    actual_size = str(os.path.getsize(os.path.join(DOWN_DIR, file_name)))
                    client_socket.sendall((actual_size).encode("utf-8"))
                    
                    client_socket.recv(BUFF_SIZE) 
                    
                    client_socket.sendall(b"OK")
                    while (data := file.read(BUFF_SIZE)):
                        client_socket.sendall(data)
                print(f"File {file_name} sent successfully.")
                
            except FileNotFoundError:
                client_socket.sendall(b"ERROR")
                print(f"File {file_name} not found")
                
                
def disconnect(host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, PORT))
        client_socket.sendall(f"DISCONNECT".encode("utf-8"))
        
        


def main():
    
    host = input("Enter the server IP address (or leave blank to auto-detect): ")
    if not host:
        host = socket.gethostbyname(socket.gethostname())
        print(f"Auto-detected server IP: {host}")
    
    while True:
        
        
        print("""
╔═══════════════════════════════════════╗
║                                       ║
║        P2P File Sharing Server        ║
║                                       ║      
╚═══════════════════════════════════════╝

Select an action:
1. GET - Download a file from the server
2. SEND - Upload a file to the server
3. LIST - List available files
""")
        
        # host = "192.168.76.113"
        command = input("Enter command: ")
        if command.upper().startswith("GET") or command.upper().startswith("SEND"):
            file_name = input("Enter file name: ")
        elif command.upper() == "LIST":
            dir_name = input("Server files list or client files list? (server/client): ")   
        
        if command.upper() == "GET":
            try:

                get_file(file_name, host)
            except FileNotFoundError:
                print(f"File {file_name} not found")
            
        elif command.upper() == "SEND":
            try:
                send_file(file_name, host) 
            except FileNotFoundError:
                print(f"File {file_name} not found")
        
        elif command.upper() == "LIST":
            list_files(dir_name,host)
                    
            
        else:
            print("Invalid command")
            
            

            
        if input("Do you want to continue? (y/n): ").lower() != "y":
            disconnect(host)
            break

if __name__ == "__main__":
    main()
