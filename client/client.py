import socket



from config import BROADCAST_PORT, BUFFER_SIZE, LOGGING_ENABLED, UDP_REQUEST_PORT, FILE_SIZE, TCP_DEST_PORT
from utils import create_udp_listener_socket, log_message, pack_udp_request, unpack_payload_message, \
    payload_success_and_speed, setup_thread_logger, FinishMessenger
import struct
import time
import threading
def listen_for_offers():
    """
    Listen for UDP broadcast messages from the server and send a request.
    """
    # Create a UDP socket for listening
    sock = create_udp_listener_socket(BROADCAST_PORT)

    print("Client started, listening for offer requests...")
    addr = None
    server_udp_port = None
    tcp_port = None
    try:
        while True:
            # Receive broadcast messages
            data, addr = sock.recvfrom(BUFFER_SIZE)

            # Parse the offer message
            magic_cookie, message_type, server_udp_port, tcp_port = struct.unpack(">LBHH", data[:9])

            # Validate the message
            if magic_cookie != 0xabcddcba or message_type != 0x2:
                print("Invalid offer message. Ignoring.")
                continue
            print(f"Received offer from {addr[0]}")
            break
    except KeyboardInterrupt:
        print("Client stopped.")
    finally:
        sock.close()
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
    """
    Receive payload messages from the server and calculate performance metrics.
    important!!!!!: 1)my_socket is the same socket that sent the request
                    2)The socket is already bound to the client's port at the invoker

    """

    my_socket.settimeout(timeout)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logger.debug(f"Receiving payloads from {server_ip}:{server_udp_port}...")

    received_segments = set()
    total_segments = None
    start_time = time.time()

    try:
        while True:
            # Receive data from the server
            data, addr = my_socket.recvfrom(BUFFER_SIZE)

            # Unpack and validate the payload
            total_segments, current_segment, _ = unpack_payload_message(data)
            logger.debug(f"Total segments: {total_segments}")
            logger.debug(f"Current segment: {current_segment}")

            # Track the received segment
            received_segments.add(current_segment)

            # Log progress
            logger.debug(f"Received segment {current_segment + 1}/{total_segments}")
    except socket.timeout:
        logger.error("Transfer complete. No data received for the timeout period.")
    finally:
        # Measure transfer performance
        end_time = time.time()
        transfer_time = end_time - start_time
        success_rate, speed = payload_success_and_speed(received_segments, total_segments, transfer_time)

        finish_messenger.udp_finished(transfer_time, speed, success_rate)#print the result


def handle_udp_transfer(server_ip, server_udp_port, thread_name, finish_messenger):
    """
    Handle the entire UDP transfer process: sending the request and receiving payloads.
    """
    request_socket = None
    try:
        # Send the UDP request
        request_socket, logger = send_udp_request(server_ip, server_udp_port)

        # Receive payloads
        receive_payloads(server_ip, server_udp_port, request_socket, logger, finish_messenger)
        print(f"Thread {thread_name} completed UDP transfer.")

    finally:
        if request_socket:
            request_socket.close()



def handle_tcp_transfer(server_ip, server_tcp_port, thread_name, finish_messenger):
    """
    Establish a TCP connection to the server and request a file transfer.
    """
    logger = setup_thread_logger()
    logger.debug(f"Connecting to {server_ip}:{server_tcp_port} for TCP transfer...")
    start_time = time.time()

    try:
        with socket.create_connection((server_ip, server_tcp_port)) as tcp_socket:
            # Send the file size request
            tcp_socket.sendall(f"{FILE_SIZE}\n".encode())
            logger.debug(f"Requested {FILE_SIZE} bytes from the server.")

            # Receive the file
            received_bytes = 0
            while True:
                data = tcp_socket.recv(4096)
                if not data:  # Connection closed
                    break
                received_bytes += len(data)
                logger.info(f"Received {len(data)} bytes ({received_bytes}/{FILE_SIZE})")

            end_time = time.time()
            transfer_time = end_time - start_time
            speed = (received_bytes * 8) / transfer_time  # Speed in bits/second

            finish_messenger.tcp_finished(transfer_time, speed) #print the result

            print(f"Thread {thread_name} completed TCP transfer.")
    except Exception as e:
        logger.error(f"Error during TCP transfer: {e}")


def full_sequence(finish_messenger, udp_threads = 2, tcp_threads = 3):
    server_ip, server_udp_port, server_tcp_port = listen_for_offers()
    if not server_ip or not server_udp_port:
        print("Failed to receive an offer. Exiting.")
        return

    #-----MULTITHREADING-----
    udp_thread_list = []
    tcp_thread_list = []

    # Launch multiple UDP threads
    for i in range(udp_threads):
        name = f"UDP-Thread-{i+1}"
        udp_thread = threading.Thread(
            target=handle_udp_transfer,
            args=(server_ip, server_udp_port, name, finish_messenger),
            name=name
        )
        udp_thread_list.append(udp_thread)
        udp_thread.start()

    # Launch multiple TCP threads
    for i in range(tcp_threads):
        name = f"TCP-Thread-{i+1}"
        tcp_thread = threading.Thread(
            target=handle_tcp_transfer,
            args=(server_ip, server_tcp_port, name, finish_messenger),
            name=name
        )
        tcp_thread_list.append(tcp_thread)
        tcp_thread.start()

    # Wait for all UDP threads to complete
    for thread in udp_thread_list:
        try:
            thread.join()
        except KeyboardInterrupt as e:
            print(f"\nClient terminated {thread.name}: {e}\n")

    # Wait for all TCP threads to complete
    for thread in tcp_thread_list:
        try:
            thread.join()
        except KeyboardInterrupt as e:
            print(f"\nClient terminated {thread.name}: {e}\n")
    print("All transfers complete, listening to offer requests")


def run_client():
    fm = FinishMessenger()
    full_sequence(fm)



if __name__ == "__main__":
    while(True):
        fm = FinishMessenger()
        full_sequence(fm)

    # Create two threads for running two clients

    # while(True):
    #
    #     client_thread_1 = threading.Thread(target=run_client, name="Client-1")
    #     client_thread_2 = threading.Thread(target=run_client, name="Client-2")
    #
    #     # Start the threads
    #     client_thread_1.start()
    #     client_thread_2.start()
    #
    #     # Wait for both threads to complete
    #     client_thread_1.join()
    #     client_thread_2.join()
    #
    #     print("Both clients have completed their transfers.")