import socket

HOST = '0.0.0.0'  # Listen all interfaces
PORT = 51398      # Port for listening
#PORT2 = 'https://azyl-51398.ag3nts.org'

# create socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    #server_socket.bind((HOST, PORT2))
    server_socket.listen()
    print(f"Serwer nasłuchuje na porcie {PORT}")

    while True:
        # Accept connection
        client_socket, client_address = server_socket.accept()
        with client_socket:
            print(f"Połączono z {client_address}")
            data = client_socket.recv(1024)
            print(f"Otrzymano: {data.decode()}")
            client_socket.sendall(b"Pobrano message")
