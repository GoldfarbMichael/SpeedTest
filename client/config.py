# UDP Configuration
TCP_DEST_PORT = 4000           # Port for TCP requests
BROADCAST_PORT = 5000  # Port to listen for broadcast messages
UDP_REQUEST_PORT = 7000           # Port for UDP requests
BUFFER_SIZE = 1024     # Size of the buffer for receiving UDP data
FILE_SIZE = 1048576      # Size of the file to request from the server
SERVER_IP = None
PAYLOAD_SEGMENT_SIZE = 512
UDP_TIMEOUT = 1
TCP_CONNECTIONS = None
UDP_CONNECTIONS = None

def set_file_size(file_size):
    global FILE_SIZE
    FILE_SIZE = file_size
