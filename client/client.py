


import socket
import struct
import sys
import time
import threading

from config import BROADCAST_PORT, BUFFER_SIZE, LOGGING_ENABLED, UDP_REQUEST_PORT, FILE_SIZE, TCP_DEST_PORT
from utils import create_udp_listener_socket, log_message, pack_udp_request, unpack_payload_message, \
    payload_success_and_speed, setup_thread_logger, FinishMessenger

terminate_flag = threading.Event()

def listen_for_offers():
    """
    Listen for UDP broadcast messages from the server and send a request.
    """
    sock = create_udp_listener_socket(BROADCAST_PORT)

    print("Client started, listening for offer requests...")
    addr = None
    server_udp_port = None
    tcp_port = None
    try:
        while not terminate_flag.is_set():
            data, addr = sock.recvfrom(BUFFER_SIZE)
            magic_cookie, message_type, server_udp_port, tcp_port = struct.unpack(">LBHH", data[:9])
            if magic_cookie != 0xabcddcba or message_type != 0x2:
                print("Invalid offer message. Ignoring.")
                continue
            print(f"Received offer from {addr[0]}")
            break
    except KeyboardInterrupt:
        print("Client stopped while listening to offers.")
    finally:
        sock.close()
        if addr is None:
            return None, None, None
        return addr[0], server_udp_port, tcp_port

def send_udp_request(server_ip, server_udp_port):
    logger = setup_thread_logger()
    request_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    request_message = pack_udp_request(FILE_SIZE)
    request_socket.bind(("", 0))
    request_socket.sendto(request_message, (server_ip, server_udp_port))
    logger.debug(f"Sent request for {FILE_SIZE} bytes to {server_ip} on UDP port {server_udp_port}")
    return request_socket, logger

def receive_payloads(server_ip, server_udp_port, my_socket, logger, finish_messenger, timeout=1):
    my_socket.settimeout(timeout)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logger.debug(f"Receiving payloads from {server_ip}:{server_udp_port}...")

    received_segments = set()
    total_segments = None
    start_time = time.time()

    try:
        while not terminate_flag.is_set():
            data, addr = my_socket.recvfrom(BUFFER_SIZE)
            total_segments, current_segment, _ = unpack_payload_message(data)
            logger.debug(f"Total segments: {total_segments}")
            logger.debug(f"Current segment: {current_segment}")
            received_segments.add(current_segment)
            logger.debug(f"Received segment {current_segment + 1}/{total_segments}")
    except socket.timeout:
        logger.error("Transfer complete. No data received for the timeout period.")
    finally:
        end_time = time.time()
        transfer_time = end_time - start_time
        success_rate, speed = payload_success_and_speed(received_segments, total_segments, transfer_time)
        finish_messenger.udp_finished(transfer_time, speed, success_rate)

def handle_udp_transfer(server_ip, server_udp_port, thread_name, finish_messenger):
    request_socket = None
    try:
        request_socket, logger = send_udp_request(server_ip, server_udp_port)
        receive_payloads(server_ip, server_udp_port, request_socket, logger, finish_messenger)
        print(f"Thread {thread_name} completed UDP transfer.")
    finally:
        if request_socket:
            request_socket.close()

def handle_tcp_transfer(server_ip, server_tcp_port, thread_name, finish_messenger):
    logger = setup_thread_logger()
    logger.debug(f"Connecting to {server_ip}:{server_tcp_port} for TCP transfer...")
    start_time = time.time()

    try:
        with socket.create_connection((server_ip, server_tcp_port)) as tcp_socket:
            tcp_socket.sendall(f"{FILE_SIZE}\n".encode())
            logger.debug(f"Requested {FILE_SIZE} bytes from the server.")
            received_bytes = 0
            while not terminate_flag.is_set():
                data = tcp_socket.recv(4096)
                if not data:
                    break
                received_bytes += len(data)
                logger.info(f"Received {len(data)} bytes ({received_bytes}/{FILE_SIZE})")
            end_time = time.time()
            transfer_time = end_time - start_time
            speed = (received_bytes * 8) / transfer_time
            finish_messenger.tcp_finished(transfer_time, speed)
            print(f"Thread {thread_name} completed TCP transfer.")
    except Exception as e:
        logger.error(f"Error during TCP transfer: {e}")

def full_sequence(finish_messenger, udp_threads=2, tcp_threads=3):

    server_ip, server_udp_port, server_tcp_port = listen_for_offers()
    if not server_ip or not server_udp_port:
        print("Failed to receive an offer. Exiting.")
        return

    udp_thread_list = []
    tcp_thread_list = []

    for i in range(udp_threads):
        name = f"UDP-Thread-{i+1}"
        udp_thread = threading.Thread(
            target=handle_udp_transfer,
            args=(server_ip, server_udp_port, name, finish_messenger),
            name=name,
            daemon=True
        )
        udp_thread_list.append(udp_thread)
        udp_thread.start()

    for i in range(tcp_threads):
        name = f"TCP-Thread-{i+1}"
        tcp_thread = threading.Thread(
            target=handle_tcp_transfer,
            args=(server_ip, server_tcp_port, name, finish_messenger),
            name=name,
            daemon=True
        )
        tcp_thread_list.append(tcp_thread)
        tcp_thread.start()

    try:
        for thread in udp_thread_list:
            thread.join()
        for thread in tcp_thread_list:
            thread.join()
    except KeyboardInterrupt:
        terminate_flag.set()
        print("Client terminated.")
    if not terminate_flag.is_set():
        print("All transfers complete, listening to offer requests")

def run_client():
    fm = FinishMessenger()
    full_sequence(fm)

if __name__ == "__main__":
    # try:
    #     while not terminate_flag.is_set():
    #         fm = FinishMessenger()
    #         full_sequence(fm)
    # except KeyboardInterrupt:
    #     terminate_flag.set()
    #     print("Client stopped at main.")
    #
    # # Create two threads for running two clients

    while not terminate_flag.is_set():
        client_thread_1 = threading.Thread(target=run_client, name="Client-1", daemon=True)
        client_thread_2 = threading.Thread(target=run_client, name="Client-2", daemon=True)

        # Start the threads
        client_thread_1.start()
        client_thread_2.start()
        try:
            client_thread_1.join()
            client_thread_2.join()
        except KeyboardInterrupt:
            terminate_flag.set()
            print("Client terminated at main.")
            sys.exit(0)
        print("Both clients have completed their transfers.")