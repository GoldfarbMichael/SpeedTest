import socket
import time
import struct
import logging
from threading import current_thread
import threading
import os
from config import PAYLOAD_SEGMENT_SIZE
def create_udp_listener_socket(port):
    """
    Create and return a UDP socket for listening to broadcasts.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))  # Bind to all available network interfaces
    return sock

def log_message(message):
    """
    Log a message with a timestamp.
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def pack_udp_request(file_size):
    """
    Pack a UDP request message into the specified binary format.

    Format:
    - Magic cookie (4 bytes): 0xabcddcba
    - Message type (1 byte): 0x3 (request)
    - File size (8 bytes): The requested file size, in bytes.
    """
    magic_cookie = 0xabcddcba
    message_type = 0x3

    # Pack the data into a binary format
    return struct.pack(">LBQ", magic_cookie, message_type, file_size)


def unpack_payload_message(data):
    """
    Unpack a payload message from the server and validate its structure.

    Format:
    - Magic cookie (4 bytes): 0xabcddcba
    - Message type (1 byte): 0x4
    - Total segment count (8 bytes)
    - Current segment number (8 bytes)
    - Payload data (remaining bytes)
    """
    # Validate minimum size (header is 21 bytes: 4+1+8+8)
    if len(data) < 21:
        raise ValueError("Payload message too short")

    # Unpack the header
    magic_cookie, message_type, total_segments, current_segment = struct.unpack(">LBQQ", data[:21])

    # Validate the magic cookie and message type
    if magic_cookie != 0xabcddcba or message_type != 0x4:
        raise ValueError("Invalid magic cookie or message type")
    # if not total_segments or not current_segment:
    #     raise ValueError("Error at total segments or current segment")

    # Extract the payload data
    payload_data = data[21:]

    return total_segments, current_segment, payload_data

def payload_success_and_speed(received_segments, total_segments, trans_time):
    """
    Calculate the success rate of received segments.

    Args:
        received_segments (set): Set of received segment numbers.
        total_segments (int): Total number of segments.
        trans_time (float): Total transfer time, in seconds.
    Returns:
        float: Percentage of successfully received packets.
    """
    if (not total_segments or not received_segments):
        print("SUUUUUUUUUUUUUKAAAAAAAAAAAA")
        return 0, 0
    success_rate = (len(received_segments) / total_segments) * 100
    speed = (len(received_segments) * PAYLOAD_SEGMENT_SIZE * 8) / trans_time
    return success_rate, speed

def setup_thread_logger(log_dir="logs"):
    """
    Set up a thread-specific logger that logs to a unique file for the current thread.

    Returns:
        logging.Logger: Thread-specific logger instance.
    """

    thread_name = current_thread().name
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)  # Ensure the log directory exists

    log_file = os.path.join(log_dir, f"{thread_name}.log")

    # Clear the log file by opening it in write mode
    with open(log_file, "w"):
        pass  # Truncate the file contents

    thread_name = current_thread().name
    logger = logging.getLogger(thread_name)
    logger.setLevel(logging.DEBUG)

    # Create a file handler for the thread
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)


    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the logger (if not already added)
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger




class FinishMessenger:
    def __init__(self):
        self.udp_counter = 0
        self.tcp_counter = 0
        self.udp_lock = threading.Lock()
        self.tcp_lock = threading.Lock()

    def udp_finished(self, total_time, total_speed, success_rate):
        with self.udp_lock:
            self.udp_counter += 1
            print(f"UDP transfer #{self.udp_counter} finished, total time: {total_time:.2f} seconds,"
                  f" total speed {total_speed:.2f} bits/second, percentage of packets received successfully:"
                  f" {success_rate:.2f}%")

    def tcp_finished(self, total_time, total_speed):
        with self.tcp_lock:
            self.tcp_counter += 1
            print(f"TCP transfer #{self.tcp_counter} finished, total time: {total_time:.2f} seconds,"
                  f" total speed {total_speed:.2f} bits/second")
