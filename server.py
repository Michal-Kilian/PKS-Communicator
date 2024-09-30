import os
import socket
from comm_funcs import send_packet, receive_packet, print_text_info, reconstruct_file
from indexes import separator, success_status_code, error_status_code


# function that handles the situation when a packet with a text fragment comes
def handle_text_fragment(packet_data, more_fragments, client_address, client_port):
    fragment_size = len(packet_data.data)

    if packet_data.fragnum <= packet_data.fragtotal:
        print("[S] Fragment with size " + str(fragment_size) + "B : " + str(packet_data.fragnum) + "/" +
              str(packet_data.fragtotal), "from", client_address, "on", client_port, "received")
        if packet_data.fragnum == packet_data.fragtotal:
            more_fragments = False

    return packet_data.data.decode(), more_fragments


# function that handles the situation when a packet with file header comes
def handle_file_header(packet_data):
    file_name = os.path.basename(packet_data.data.decode().split(separator)[0])
    file_path = packet_data.data.decode().split(separator)[0]
    file_size = int(packet_data.data.decode().split(separator)[1])
    return file_name, file_path, file_size


# function that handles the situation when a packet with a file fragment comes
def handle_file_fragment(packet_data, more_fragments, client_address, client_port, status_code):
    fragment_size = len(packet_data.data)

    if packet_data.fragnum <= packet_data.fragtotal:
        print("[S] Fragment with size " + str(fragment_size) + "B : " + str(packet_data.fragnum) + "/" +
              str(packet_data.fragtotal), "from", client_address, "on", client_port, "received")
        if packet_data.fragnum == packet_data.fragtotal and status_code == success_status_code:
            more_fragments = False

    return packet_data.data, more_fragments


# Server class that receives texts or files
class Server:
    HOST: str
    PORT: int
    buffer_size: int
    udp_server_socket: socket
    clients_connected: dict
    listening: bool

    # initialize function that starts
    # the setup of a server
    # and the listening loop
    def __init__(self, host, port):
        self.setup_server(host, port)
        self.listening_loop()

    # function that stores important server information inside this class
    def setup_server(self, host, port):
        self.HOST = host
        self.PORT = port
        self.udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_server_socket.bind((self.HOST, self.PORT))
        self.udp_server_socket.settimeout(5)
        self.buffer_size = 8192
        self.clients_connected = {}
        self.listening = True
        print("[S] UDP server listening on IP:", self.HOST, "and port:", self.PORT)

    # function that listens for any packets coming
    # and responds to them accordingly
    def listening_loop(self):
        text_fragments = ""
        file_fragments = {}
        file_name = ""
        file_size = 0
        more_fragments = True

        while self.listening:

            try:
                packet_data, client_address, client_port, status_code = receive_packet(self.udp_server_socket,
                                                                                       self.buffer_size)
            except TimeoutError:
                continue

            print("Receiving:", packet_data.data)
            print("Status code:", status_code)

            if status_code == success_status_code:
                send_packet("ACK", "NO-DATATYPE", 1, 1, "", self.udp_server_socket, client_address, client_port)
                if packet_data.commtype == "SYN" and packet_data.datatype == "NO-DATATYPE":
                    if (client_address, client_port) not in self.clients_connected.keys():
                        self.clients_connected.update({(client_address, client_port): True})
                        print("[S] Connected to client with IP:", client_address, "on port:", client_port)
                    continue

                if packet_data.commtype == "FIN":
                    self.udp_server_socket.close()
                    self.listening = False
                    return "exit"

                if packet_data.datatype == "TEXT":
                    text_frag, more_fragments = handle_text_fragment(packet_data, more_fragments, client_address,
                                                                     client_port)
                    text_fragments += text_frag

                if packet_data.datatype == "FILE-HEADER":
                    file_name, file_path, file_size = handle_file_header(packet_data)

                if packet_data.datatype == "FILE":
                    file_frag, more_fragments = handle_file_fragment(packet_data, more_fragments, client_address,
                                                                     client_port, status_code)
                    print("adding:", packet_data.data)
                    file_fragments[packet_data.fragnum] = packet_data.data
                    print("file_fragments:", file_fragments)

                if not more_fragments:
                    more_fragments = True
                    if packet_data.datatype == "TEXT":
                        text_fragments = print_text_info("RECEIVED", text_fragments, client_address, client_port)
                    elif packet_data.datatype == "FILE":
                        file_fragments = reconstruct_file(file_name, file_size, file_fragments, client_address,
                                                          client_port)

            elif status_code == error_status_code:
                send_packet("FIN", "NO-DATATYPE", 1, 1, "", self.udp_server_socket, client_address, client_port)
                print("[S] Fragment was not received correctly because the checksum values do not match, asking to "
                      "resend the message")
                continue
