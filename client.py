import os.path
import socket
import time
from threading import Thread
from comm_funcs import send_packet, receive_packet, print_file_info, print_text_info
from indexes import separator, error_status_code, success_status_code


# function that lets you pick the fragment size for your message or file
def fragment_size_loop():
    fragment_size_correct = False

    while not fragment_size_correct:
        fragment_size = input("[C] Fragment size (min 5B/max 8000B): ")
        if fragment_size == "":
            print("[C] Please fill in the fragment size")
            continue
        elif int(fragment_size) < 5:
            print("[C] Fragment size has to be at least 5B, try again")
            continue
        elif int(fragment_size) > 8000:
            print("[C] Fragment size has to be a maximum of 8000B, try, again")
        else:
            return int(fragment_size)


# function that prepares the file path
# by removing the quotation marks if there were any
def prepare_file_path(file_path):
    if file_path[0] == '"' and file_path[-1] == '"':
        return file_path[1:-1]


class Client:
    TARGET_HOST: str
    TARGET_PORT: int
    buffer_size: int
    udp_client_socket: socket
    connection_established: bool

    # initialize function that starts
    # the setup of a client
    # and the establishment of connection
    def __init__(self, host, port):
        self.setup_client(host, port)
        self.establish_connection()

    # function that stores important client information inside this class
    def setup_client(self, host, port):
        self.TARGET_HOST = host
        self.TARGET_PORT = port
        self.udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udp_client_socket.settimeout(5)
        self.buffer_size = 8192
        self.connection_established = False

    # function that is used to establish the connection between a server and a client
    def establish_connection(self):
        timeout = 0

        while not self.connection_established and timeout != 3:

            send_packet("SYN", "NO-DATATYPE", 1, 1, "", self.udp_client_socket, self.TARGET_HOST,
                        self.TARGET_PORT)
            try:
                packet_data, client_address, client_port, status_code = receive_packet(self.udp_client_socket,
                                                                                       self.buffer_size)
                if packet_data.commtype == "ACK":
                    self.connection_established = True
                elif packet_data.commtype == "FIN":
                    timeout += 1
                    continue

            except TimeoutError:
                timeout += 1
                continue
            except ConnectionResetError:
                time.sleep(3)
                timeout += 1
                continue

        if self.connection_established:
            print("[C] Connected to server with IP:", self.TARGET_HOST, "on port:", self.TARGET_PORT)
            # keep_alive_thread = Thread(target=self.client_keep_alive)
            # keep_alive_thread.start()
            self.command_loop()
        elif timeout == 3:
            print("[C] Could not connect to", self.TARGET_HOST, "on", str(self.TARGET_PORT) + ": Timeout error")
            return

    # function that executes user commands
    def command_loop(self):
        loop = True
        while loop:
            command = input("[C] Command (send/change): ")

            if command == "send":
                choice = input("[C] Choose (text/file): ")
                if choice == "text":
                    text = input("[C] Text: ")
                    self.send_text(text, fragment_size_loop())
                elif choice == "file":
                    file_path = input("[C] File path: ")
                    self.send_file(prepare_file_path(file_path), fragment_size_loop())
                else:
                    continue

            elif command == "change":
                loop = False
                if self.change():
                    self.connection_established = False
                    return
                else:
                    print("[C] The server did not respond with ACK, changing failed")
                    continue

    # function that handles the sending of a text
    def send_text(self, text, fragment_size):
        text_bytes_length = len(text.encode())
        fragtotal = text_bytes_length // fragment_size
        if text_bytes_length % fragment_size != 0:
            fragtotal += 1

        fragnum = 1
        while fragnum <= fragtotal:
            ack_received = False
            timeout = 0

            while not ack_received and timeout != 3:

                send_packet("NO-COMMTYPE", "TEXT", fragnum, fragtotal,
                            text[(fragnum - 1) * fragment_size: fragnum * fragment_size],
                            self.udp_client_socket, self.TARGET_HOST, self.TARGET_PORT)
                print("[C] Fragment " + str(fragnum) + "/" + str(fragtotal) + " sent")

                try:
                    packet_data, server_address, server_port, status_code = receive_packet(self.udp_client_socket,
                                                                                           self.buffer_size)
                    if packet_data.commtype == "ACK":
                        ack_received = True
                        continue
                    elif packet_data.commtype == "FIN":
                        timeout += 1
                        continue

                except TimeoutError:
                    timeout += 1
                    continue
                except ConnectionResetError:
                    time.sleep(3)
                    timeout += 1
                    continue

            if ack_received:
                fragnum += 1
                continue
            elif timeout == 3:
                print("[C] The server did not respond with ACK three times, sending stopped")

        print_text_info("SENT", text, self.TARGET_HOST, self.TARGET_PORT)

    # function that handles the sending of a file
    def send_file(self, file_path, fragment_size):
        if not os.path.exists(file_path):
            print("[C] A file with this path does not exist")
            return

        file_size = os.path.getsize(file_path)
        fragtotal = file_size // fragment_size
        if file_size % fragment_size != 0:
            fragtotal += 1

        send_packet("NO-COMMTYPE", "FILE-HEADER", 1, 1, str(file_path) + separator + str(file_size),
                    self.udp_client_socket, self.TARGET_HOST, self.TARGET_PORT)

        file_fragments = fill_file_fragments(file_path, fragment_size)

        print(file_fragments)

        for fragnum in file_fragments.keys():
            timeout = 0

            while True:
                try:
                    send_packet("NO-COMMTYPE", "FILE", fragnum, fragtotal, file_fragments.get(fragnum),
                                self.udp_client_socket, self.TARGET_HOST, self.TARGET_PORT)

                    packet_data, server_address, server_port, status_code = receive_packet(self.udp_client_socket,
                                                                                           self.buffer_size)

                    if status_code == error_status_code:
                        print("[C] Server sent a corrupted packet, resending")
                        continue
                    if packet_data.commtype == "ACK":
                        print("[C] Fragment with size " + str(fragment_size) + "B : " + str(fragnum) + "/" +
                              str(fragtotal) + " sent")
                        break
                    elif packet_data.commtype == "FIN":
                        continue

                except TimeoutError:
                    timeout += 1
                    if timeout == 3:
                        print("[C] The server did not respond 3 times")
                        return
                    continue

        print_file_info("SENT", self.TARGET_HOST, self.TARGET_PORT, file_path, file_size)

    # function that handles the change situation
    def change(self):
        ack_received = False
        timeout = 0

        while not ack_received or not timeout == 3:

            send_packet("FIN", "NO-DATATYPE", 1, 1, "NO-DATA", self.udp_client_socket, self.TARGET_HOST,
                        self.TARGET_PORT)

            try:
                packet_data, server_address, server_port, status_code = receive_packet(self.udp_client_socket,
                                                                                       self.buffer_size)
                if packet_data.commtype == "ACK":
                    ack_received = True
                    self.udp_client_socket.close()
                    return True
                else:
                    continue
            except TimeoutError:
                timeout += 1
                if timeout == 3:
                    print("Timed out")
                    return False
                else:
                    continue
            except ConnectionResetError:
                time.sleep(3)
                timeout += 1
                if timeout == 3:
                    print("Timed out")
                    return False
                else:
                    continue

    # function that performs the keep alive while the client is connected
    def client_keep_alive(self):

        while self.connection_established:
            ack_received = False
            timeout = 0

            time.sleep(5)

            while not ack_received and timeout != 3:

                send_packet("SYN", "NO-DATATYPE", 1, 1, "", self.udp_client_socket, self.TARGET_HOST,
                            self.TARGET_PORT)

                try:
                    packet_data, server_address, server_port, status_code = receive_packet(self.udp_client_socket,
                                                                                           self.buffer_size)

                    if packet_data.commtype == "ACK" and packet_data.datatype == "NO-DATATYPE":
                        ack_received = True
                    else:
                        timeout += 1

                except TimeoutError:
                    timeout += 1
                    continue
                except ConnectionResetError:
                    time.sleep(3)
                    timeout += 1
                    continue
                except OSError:
                    return

            if ack_received:
                continue
            elif timeout == 3:
                print("[C] Connection with", self.TARGET_HOST, "on", self.TARGET_PORT, "timed out")
                self.connection_established = False
                return


# Client class that sends texts or files
def fill_file_fragments(file_path, fragment_size):
    file_read = False
    file_fragments = {}
    fragnum = 0

    with open(file_path, "rb") as f:

        while not file_read:
            bytes_read = f.read(fragment_size)
            if bytes_read:
                fragnum += 1
                file_fragments.update({fragnum: bytes_read})
            else:
                file_read = True

    return file_fragments
