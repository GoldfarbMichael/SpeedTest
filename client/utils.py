import socket
import time
import struct

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

    # Extract the payload data
    payload_data = data[21:]

    return total_segments, current_segment, payload_data

def calculate_success_rate(received_segments, total_segments):
    """
    Calculate the success rate of received segments.

    Args:
        received_segments (set): Set of received segment numbers.
        total_segments (int): Total number of segments.

    Returns:
        float: Percentage of successfully received packets.
    """
    return (len(received_segments) / total_segments) * 100