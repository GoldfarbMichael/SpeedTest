import socket
from config import BROADCAST_PORT, BUFFER_SIZE, LOGGING_ENABLED, UDP_REQUEST_PORT
from utils import create_udp_listener_socket, log_message, pack_udp_request, unpack_payload_message, calculate_success_rate
import struct
import time

def listen_for_offers():
    """
    Listen for UDP broadcast messages from the server and print the received offers.
    """
    # Create a UDP socket for listening
    sock = create_udp_listener_socket(BROADCAST_PORT)

    if LOGGING_ENABLED:
        log_message(f"Client started, listening for offer requests on port {BROADCAST_PORT}...")

    try:
        while True:
            # Receive data from the server
            data, addr = sock.recvfrom(BUFFER_SIZE)
            offer_message = data.decode()

            if LOGGING_ENABLED:
                log_message(f"Received offer from {addr[0]}: {offer_message}")
    except KeyboardInterrupt:
        if LOGGING_ENABLED:
            log_message("Client stopped.")
    finally:
        sock.close()

def listen_for_offers_and_request(file_size):
    """
    Listen for UDP broadcast messages from the server and send a request.
    """
    # Create a UDP socket for listening
    sock = create_udp_listener_socket(BROADCAST_PORT)

    print(f"Listening for offers on port {BROADCAST_PORT}...")

    try:
        while True:
            # Receive broadcast messages
            data, addr = sock.recvfrom(BUFFER_SIZE)

            # Parse the offer message
            magic_cookie, message_type, udp_port, tcp_port = struct.unpack(">LBHH", data[:9])

            # Validate the message
            if magic_cookie != 0xabcddcba or message_type != 0x2:
                print("Invalid offer message. Ignoring.")
                continue

            print(f"Received offer from {addr[0]}: UDP={udp_port}, TCP={tcp_port}")

            # Send a UDP request
            request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            request_message = pack_udp_request(file_size)
            request_socket.sendto(request_message, (addr[0], udp_port))
            receive_payloads(addr[0], udp_port)
            print(f"Sent request for {file_size} bytes to {addr[0]} on UDP port {udp_port}")

            # Exit after sending the request
            break
    except KeyboardInterrupt:
        print("Client stopped.")
    finally:
        sock.close()

def receive_payloads(server_ip, udp_port, timeout=1):
    """
    Receive payload messages from the server and calculate performance metrics.

    Args:
        server_ip (str): Server's IP address.
        udp_port (int): Server's UDP port.
        timeout (int): Timeout in seconds to detect the end of the transfer.
    """
    # Create a UDP socket for receiving payloads
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_REQUEST_PORT))  # Bind to the request port
    sock.settimeout(timeout)

    print(f"Receiving payloads from {server_ip}:{udp_port}...")

    received_segments = set()
    total_segments = None
    start_time = time.time()

    try:
        while True:
            # Receive data from the server
            data, addr = sock.recvfrom(BUFFER_SIZE)

            # Unpack and validate the payload
            total_segments, current_segment, _ = unpack_payload_message(data)

            # Track the received segment
            received_segments.add(current_segment)

            # Log progress
            print(f"Received segment {current_segment + 1}/{total_segments}")
    except socket.timeout:
        print("Transfer complete. No data received for the timeout period.")
    finally:
        # Measure transfer performance
        end_time = time.time()
        transfer_time = end_time - start_time
        # success_rate = calculate_success_rate(received_segments, total_segments)

        print(f"Transfer complete:")
        print(f"- Total time: {transfer_time:.2f} seconds")
        # print(f"- Success rate: {success_rate:.2f}%")
        # print(f"- Segments received: {len(received_segments)}/{total_segments}")

        sock.close()

if __name__ == "__main__":
    listen_for_offers_and_request(1024)