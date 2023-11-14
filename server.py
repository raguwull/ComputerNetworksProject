import socket
import threading
import math

client1_socket = None
client2_socket = None
lowest_mtu1 = float('inf')
lowest_mtu2 = float('inf')
lowest_mtu_lock = threading.Lock()

def send_data_with_fragments(client_socket, data, mtu):
    datasize = len(data) + 20
    no_of_packets = math.ceil((datasize - 20) / (mtu - 20))

    client_socket.send(f"\n==============================================\n{no_of_packets} fragments were created for the data".encode("utf-8"))
    client_socket.send("\n----------------------------------------------".encode("utf-8"))
    client_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format("#", "TOTAL LENGTH", "FLAG", "OFFSET").encode("utf-8"))
    client_socket.send("\n----------------------------------------------".encode("utf-8"))

    for i in range(1, no_of_packets):
        length = mtu
        flags = 1
        offset = math.ceil((mtu - 20) * (i - 1) / 8)
        client_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format(i, length, flags, offset).encode("utf-8"))
        client_socket.send("\n----------------------------------------------".encode("utf-8"))

    final_length = datasize - (mtu - 20) * (no_of_packets - 1)
    final_flags = 0
    final_offset = ((mtu - 20) * (no_of_packets - 1)) / 8

    client_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format(no_of_packets, final_length, final_flags, final_offset).encode("utf-8"))
    client_socket.send("\n----------------------------------------------\n".encode("utf-8"))

    i = 1

    while data != '':
        fragment_data = "\nFragment-" + str(i) + ": |" + '#' * 20 + '|' + data[:mtu - 20] + '|'
        client_socket.send(fragment_data.encode("utf-8"))
        i += 1
        data = data[mtu - 20:]

    client_socket.send("==============================================\n".encode("utf-8"))


def handle_client(client_socket):
    global client1_socket, client2_socket, lowest_mtu1, lowest_mtu2

    client_address = client_socket.getpeername()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    request = client_socket.recv(65536)
    request = request.decode("utf-8")
    mtu_bytes = int(request)

    with lowest_mtu_lock:
        if mtu_bytes < lowest_mtu1:
            lowest_mtu2 = lowest_mtu1
            client2_socket = client1_socket

            lowest_mtu1 = mtu_bytes
            client1_socket = client_socket

        elif mtu_bytes < lowest_mtu2:
            lowest_mtu2 = mtu_bytes
            client2_socket = client_socket

    print(f"MTU byte size from client {client_address[0]}:{client_address[1]}: {mtu_bytes}")

    while True:
        response = input("\nEnter your data to transmit: ")

        if response.lower() == "exit":
            client_socket.send(response.encode("utf-8"))
            break

        if len(response) >= lowest_mtu1:
            send_data_with_fragments(client1_socket, response, lowest_mtu1)
            send_data_with_fragments(client2_socket, response, lowest_mtu2)
        else:
            client1_socket.send("\n==============================================\nSince MTU > DATA SIZE, the packet moves on to the next encapsulation phase without fragmentation".encode("utf-8"))
            client2_socket.send("\n==============================================\nSince MTU > DATA SIZE, the packet moves on to the next encapsulation phase without fragmentation".encode("utf-8"))

            datasize = len(response) + 20
            client1_socket.send("\n----------------------------------------------".encode("utf-8"))
            client2_socket.send("\n----------------------------------------------".encode("utf-8"))
            client1_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format("#", "TOTAL LENGTH", "FLAG", "OFFSET").encode("utf-8"))
            client2_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format("#", "TOTAL LENGTH", "FLAG", "OFFSET").encode("utf-8"))
            client1_socket.send("\n----------------------------------------------".encode("utf-8"))
            client2_socket.send("\n----------------------------------------------".encode("utf-8"))
            client1_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format(1, datasize, 0, 0).encode("utf-8"))
            client2_socket.send("\n{:<2} {:<20} {:<10} {:<10}".format(1, datasize, 0, 0).encode("utf-8"))
            client1_socket.send("\n----------------------------------------------".encode("utf-8"))
            client2_socket.send("\n----------------------------------------------".encode("utf-8"))
            client1_socket.send("\n==============================================\n".encode("utf-8"))
            client2_socket.send("\n==============================================\n".encode("utf-8"))
            data = "\nFragment-1: |" + '#' * 20 + '|' + response + '|' + '\n'
            client1_socket.send(data.encode("utf-8"))
            client2_socket.send(data.encode("utf-8"))

    client_socket.close()
    print(f"Connection to {client_address[0]}:{client_address[1]} closed")


def run_server(server_ip="127.0.0.1", port=8000):
    global client1_socket, client2_socket

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, port))
    server.listen(2)  # Allow up to 2 clients

    print(f"Listening on {server_ip}:{port}")

    while True:
        client_socket, _ = server.accept()

        if client1_socket is None:
            client1_socket = client_socket
        elif client2_socket is None:
            client2_socket = client_socket

        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


run_server()
