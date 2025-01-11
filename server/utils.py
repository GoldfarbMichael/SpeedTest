import socket
import struct

def create_udp_broadcast_socket():
    """Create and return a UDP socket configured for broadcasting."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return sock

def pack_offer_message(udp_port, tcp_port):
    """
    Pack an offer message into the specified binary format.

    Format:
    - Magic cookie (4 bytes): 0xabcddcba
    - Message type (1 byte): 0x2
    - Server UDP port (2 bytes)
    - Server TCP port (2 bytes)
    """
    return struct.pack(">LBHH", 0xabcddcba, 0x2, udp_port, tcp_port)

def pack_payload_message(segment_count, current_segment, payload_size):
    """
    Pack a payload message into the specified binary format.

    Format:
    - Magic cookie (4 bytes): 0xabcddcba
    - Message type (1 byte): 0x4
    - Total segment count (8 bytes)
    - Current segment number (8 bytes)
    - Payload data (variable size)
    """
    magic_cookie = 0xabcddcba
    message_type = 0x4

    # Construct the header
    header = struct.pack(">LBQQ", magic_cookie, message_type, segment_count, current_segment)

    # Generate dummy payload data of the specified size
    payload_data = b'X' * payload_size  # 'X' is a placeholder byte

    return header + payload_data