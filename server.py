import socket
import threading
import os
from datetime import datetime

class Server:
    """
    Multi-thread TCP communication that handles max of 3 clients,
    supports to check status, list available files, request transfers
    """
    def __init__(self, host="localhost", port=8000, max_clients=3):
        self.host = host    #server ip host
        self.port = port    #unused port

        self.max_clients = max_clients  #max 3 clients
        self.clients = {}        #holds connection times
        self.file_repo = os.getcwd() #holds files
        print("Server initialized")

    def start(self): #starts server, waits for connections, and spawns threads
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)

        print("Waiting for client connection")

        while True:
            client_socket, client_address = self.server_socket.accept()

            #check if server full and error handle
            if len(self.clients) >= self.max_clients:
                print("Server full", client_address)
                try:
                    client_socket.send(b"server full")
                except Exception as e:
                    print("Error sending 'server full' message:", e)
                client_socket.close()
                continue

            #assign client name in Client01 form
            client_name = "Client" + str(len(self.clients) + 1).zfill(2)

            connection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #connection time call
            self.clients[client_name] = (connection_time, None)

            try:
                client_socket.send(("Enter " + client_name).encode())
            except Exception as e:
                print("Error sending client name:", e)
                client_socket.close()
                continue

            print(client_name, "connected at", connection_time)

            #thread handling, allows exit
            threading.Thread(
                target=self.handle_client,
                args=(client_socket, client_name),
                daemon=True
            ).start()

    def handle_client(self, client_socket, client_name):
        #handles responses, terminal client comms
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message or message.strip() == "exit":
                    break

                if message == "status": #status msg
                    response = self.get_cache_status()
                    client_socket.send(response.encode())

                elif message == "list": #lists files
                    response = self.get_file_list()
                    client_socket.send(response.encode())

                elif message.startswith("file:"):
                    filename = message.split(":", 1)[1].strip()
                    #returns filename(or not) if error
                    result = self.send_file(filename, client_socket)
                    if result is not None:
                        client_socket.send(result.encode())
                else:
                    #returns ACK append
                    response = f"{message} ACK"
                    client_socket.send(response.encode())

            except Exception as e:
                print("Error handling client", client_name, ":", e)
                break

        #disconnect time
        disconnect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clients[client_name] = (self.clients[client_name][0], disconnect_time)
        client_socket.close()

        del self.clients[client_name]  #removes client from list cleanly
        print(client_name, "disconnected at", disconnect_time)

    def get_cache_status(self):
        #generates status connec/disconnect time
        result = []
        for client, (conn_time, disc_time) in self.clients.items():
            status = disc_time if disc_time else "still here"
            result.append(f"{client} connected: {conn_time}, disconnected: {status}")
        return "\n".join(result) if result else "No clients"

    def get_file_list(self):
      #returns list of files in repo
        try:
            files = os.listdir(self.file_repo)
            return "\n".join(files) if files else "No files available"
        except Exception as e:
            print("Error listing files:", e)
            return "Error listing files."

    def send_file(self, filename, client_socket):
        #sends requested file to client, with header, chunk data
        #if not exist, returns error
        filepath = os.path.join(self.file_repo, filename)
        print("Sending file:", filename)

        if not os.path.isfile(filepath):
            return "File not found."

        try:
            with open(filepath, 'rb') as file:
                #header file transfer
                client_socket.send(("file:" + filename).encode())
                #send chunks
                chunk = file.read(1024)
                while chunk:
                    client_socket.send(chunk)
                    chunk = file.read(1024)
                #end signla
                client_socket.send(b"EOF")
            return None #end
        except Exception as e:
            print("Error sending file:", e)
            return "Error sending file."

if __name__ == "__main__":
    server = Server()
    server.start()
