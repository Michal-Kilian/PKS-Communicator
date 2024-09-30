import collections
import os
import random
from typing import Tuple
from zlib import crc32
from packet_creator import PacketCreator
from packet_data import PacketData
from packet_translator import PacketTranslator
from indexes import header_start, data_start, success_status_code, error_status_code, checksum_start


# function that sends the desired packet to the chosen destination
def send_packet(commtype, datatype, fragnum, fragtotal, data, udp_socket, target_host, target_port):
    packet_data = PacketData(commtype, datatype, fragnum, fragtotal, data)
    packet = PacketCreator.create_packet(packet_data)
    try:
        udp_socket.sendto(packet, (target_host, target_port))
    except OSError:
        return


# function that receives a packet from the desired destination
def receive_packet(udp_socket, buffer_size) -> Tuple[PacketData, str, int, int]:
    packet, (client_address, client_port) = udp_socket.recvfrom(buffer_size)
    packet_data, checksum = PacketTranslator.translate_packet(packet)

    if not compare_checksum(checksum, packet):
        return packet_data, client_address, client_port, error_status_code

    return packet_data, client_address, client_port, success_status_code


# function that calculates the checksum value from a packet
def get_checksum(packet) -> int:
    HEADER_WITHOUT_CHECKSUM = packet[header_start: checksum_start]
    DATA = packet[data_start:]
    CHECKSUM = crc32(HEADER_WITHOUT_CHECKSUM + DATA)

    return CHECKSUM


# function that compares the checksum values
def compare_checksum(checksum1, packet) -> bool:
    return checksum1 == get_checksum(packet)


# function that reconstructs the file from a dictionary full of file fragments
def reconstruct_file(file_path, file_size, file_fragments, client_address, client_port) -> dict:
    file_name = os.path.basename(file_path)

    sorted_by_fragnum = collections.OrderedDict(sorted(file_fragments.items()))

    with open(file_name, "wb") as f:

        for fragment in sorted_by_fragnum.values():
            f.write(fragment)

    file_path = os.getcwd() + "\\" + file_name

    print_file_info("RECEIVED", client_address, client_port, file_path, file_size)
    return {}


# function that prints the information about a text sent or received
def print_text_info(sent_or_received, text_fragments, address, port) -> str:
    icon = ""
    if sent_or_received == "SENT":
        icon = "[C]"
        print(icon, "Text sent to IP:", address, "on port:", port)
    elif sent_or_received == "RECEIVED":
        icon = "[S]"
        print(icon, "Text received from IP:", address, "on port:", port)
    print(icon, "Text:", text_fragments)
    print(icon, "Text size:", str(len(text_fragments)) + "B")
    return ""


# function that prints the information about a file sent or received
def print_file_info(sent_or_received, address, port, file_path, file_size):
    icon = ""
    if sent_or_received == "SENT":
        icon = "[C]"
        print(icon, "File sent to IP:", address, "on port:", port)
    elif sent_or_received == "RECEIVED":
        icon = "[S]"
        print(icon, "File received from IP:", address, "on port:", port)
    print(icon, "File name:", os.path.basename(file_path))
    print(icon, "File path:", file_path)
    print(icon, "File size:", str(file_size) + "B")
