# client1.py

import socket

def run_client(server_ip="127.0.0.1", server_port=8000):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    msg = input("Client 1 - Enter byte size of MTU: ")
    client.send(msg.encode("utf-8")[:65536])

    while True:
        response = client.recv(65536)
        response = response.decode("utf-8")

        if response.lower() == "exit" or msg.lower() == "exit":
            break

        print(response)

    client.close()
    print("Client 1 - Connection to server closed")

run_client()
