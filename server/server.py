import socket
import time
from config import BROADCAST_IP, BROADCAST_PORT, UDP_REQUEST_PORT, TCP_REQUEST_PORT, BROADCAST_INTERVAL, MAX_CONNECTIONS, SERVERS_IP
from utils import create_udp_broadcast_socket, pack_offer_message, pack_payload_message
import threading
import struct
# def start_server():
#     # Get the server's IP address
#     hostname = socket.gethostname()
#     server_ip = socket.gethostbyname(hostname)
#
#     # Create UDP broadcast socket
#     broadcast_socket = utils.create_udp_broadcast_socket()
#
#     # Format the offer message
#     offer_message = config.OFFER_MESSAGE.format(ip=server_ip)
#     print(offer_message)
#
#     # Broadcast the message every second
#     try:
#         while True:
#             broadcast_socket.sendto(offer_message.encode(), (config.BROADCAST_IP, BROADCAST_PORT))
#             print(f"Broadcasting: {offer_message}")
#             time.sleep(BROADCAST_INTERVAL)
#     except KeyboardInterrupt:
#         print("\nServer stopped.")
#     finally:
#         broadcast_socket.close()
#

def broadcast_offers():
    """Broadcast offer messages via UDP on a separate thread."""
    # Create a UDP socket for broadcasting
    sock = create_udp_broadcast_socket()
    offer_message = pack_offer_message(UDP_REQUEST_PORT, TCP_REQUEST_PORT)

    try:
        while True:
            # Send the offer message as a broadcast
            sock.sendto(offer_message, (BROADCAST_IP, BROADCAST_PORT))
            print(f"Broadcasting offer: UDP={UDP_REQUEST_PORT}, TCP={TCP_REQUEST_PORT}")
            time.sleep(BROADCAST_INTERVAL)
    except KeyboardInterrupt:
        print("Stopping offer broadcast...")
    finally:
        sock.close()

def handle_tcp_connection(client_socket, address):
    """Handle a single TCP connection."""
    print(f"New TCP connection from {address}")
    try:
        # Read the requested file size
        data = client_socket.recv(1024).decode().strip()
        file_size = int(data)  # Expecting a numeric string followed by '\n'
        print(f"Client requested file size: {file_size} bytes")

        # Send the requested data back as a string of 'X's
        client_socket.sendall(b'X' * file_size)
        print(f"Sent {file_size} bytes to {address}")
    except Exception as e:
        print(f"Error handling TCP connection from {address}: {e}")
    finally:
        client_socket.close()

def start_tcp_server():
    """Start a TCP server for handling client requests."""
    import socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", TCP_REQUEST_PORT))
    server_socket.listen(MAX_CONNECTIONS)
    print(f"TCP server listening on IP address {SERVERS_IP}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            threading.Thread(target=handle_tcp_connection, args=(client_socket, address)).start()
    except KeyboardInterrupt:
        print("Stopping TCP server...")
    finally:
        server_socket.close()


def handle_udp_requests():
    """
    Handle incoming UDP requests from clients and respond with payload messages.
    """
    # Create a UDP socket for handling client requests
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", UDP_REQUEST_PORT))
    print(f"UDP server listening for requests on port {UDP_REQUEST_PORT}")

    try:
        while True:
            # Receive a request from a client
            data, client_address = server_socket.recvfrom(1024)
            print(f"Received UDP request from {client_address}")

            # Validate the request
            if len(data) < 13:  # Minimum size for a valid request packet
                print("Invalid UDP request (too short). Ignored.")
                continue

            # Parse the request packet
            magic_cookie, message_type, requested_size = struct.unpack(">LBQ", data[:13])
            if magic_cookie != 0xabcddcba or message_type != 0x3:
                print("Invalid magic cookie or message type. Ignored.")
                continue

            print(f"Valid request received: {requested_size} bytes requested")

            # Calculate the number of segments
            segment_size = 512  # Fixed size of each payload segment
            segment_count = (requested_size + segment_size - 1) // segment_size  # Ceiling division

            # Send each segment to the client
            for segment_number in range(segment_count):
                payload = pack_payload_message(segment_count, segment_number, segment_size)
                server_socket.sendto(payload, client_address)

            print(f"Finished sending {segment_count} segments to {client_address}")
    except KeyboardInterrupt:
        print("Stopping UDP server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Start broadcasting offers in a separate thread
    broadcast_thread = threading.Thread(target=broadcast_offers, daemon=True)
    broadcast_thread.start()

    udp_thread = threading.Thread(target=handle_udp_requests, daemon=True)
    udp_thread.start()
    # Start the TCP server
    start_tcp_server()