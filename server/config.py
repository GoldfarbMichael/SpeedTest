import socket
# Networking Configuration
  # Broadcast address
TCP_REQUEST_PORT = 4000           # Port for TCP requests
BROADCAST_PORT = 5000             # Port for broadcasting offers
UDP_REQUEST_PORT = 6000           # Port for UDP requests

# Packet Configuration
MAGIC_COOKIE = 0xabcddcba         # Magic cookie value
OFFER_MESSAGE_TYPE = 0x2          # Offer message type
BROADCAST_INTERVAL = 1            # Interval between broadcast messages (in seconds)
SEGMENT_SIZE = 512                # Size of each payload segment

# General Configuration
MAX_CONNECTIONS = 10              # Maximum number of simultaneous connections




def get_own_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address
def set_broadcast_ip():
    global BROADCAST_IP
    b_ip = get_own_ip()[:-3]+"255"
    BROADCAST_IP = b_ip
    return b_ip
BROADCAST_IP = set_broadcast_ip()




