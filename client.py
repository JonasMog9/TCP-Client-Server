import socket

class Client:
    """
     TCP client that connects to server supports to check status, list available files, request transfers
    """
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port

    def start(self):
        #connects client to server
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to {self.host} on port {self.port}")

            #receives msg from server
            initial_message = self.client_socket.recv(1024).decode()
            print(initial_message)
        except Exception as e:
            print("Error connecting to the server:", e)
            return

        #message snding
        while True:
            message = input("Enter message (or type 'exit' to disc): ").strip()

            if not message:
                print("Please enter a message.")
                continue

            try:
                self.client_socket.send(message.encode())
            except Exception as e:
                print("Error sending:", e)
                break

            if message.lower() == "exit":
                print("Exiting")
                break

            try:
                response = self.client_socket.recv(1024).decode()
            except Exception as e:
                print("Error receiving response:", e)
                break

            #handles file request / download
            if message.startswith("file:"):
                filename = message.split(":", 1)[1].strip()
                self.receive_file(filename, response)
            else:
                print("Server says:", response)

        self.client_socket.close()
        print("Disconnected")

    def receive_file(self, filename, response):
        #receives file from server and svaes, error handles
        if response == "File not found.":
            print("File not found.")
            return

        try:
            with open(filename, "wb") as file:
                while True:
                    data = self.client_socket.recv(1024)
                    if data == b"EOF":
                        break
                    file.write(data)
            print(f"File received: {filename}")
        except Exception as e:
            print("Error receiving file:", e)

if __name__ == "__main__":
    client = Client()
    client.start()
