import socket
# Networking Configuration
BROADCAST_IP = "255.255.255.255"  # Broadcast address
BROADCAST_PORT = 5000             # Port for broadcasting offers
UDP_REQUEST_PORT = 6000           # Port for UDP requests
TCP_REQUEST_PORT = 7000           # Port for TCP requests

# Packet Configuration
MAGIC_COOKIE = 0xabcddcba         # Magic cookie value
OFFER_MESSAGE_TYPE = 0x2          # Offer message type
BROADCAST_INTERVAL = 1            # Interval between broadcast messages (in seconds)

# General Configuration
MAX_CONNECTIONS = 10              # Maximum number of simultaneous connections



def get_own_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

SERVERS_IP = get_own_ip()