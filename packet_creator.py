import json
from zlib import crc32


# function that loads the values
# from an external file
def load_values_file():
    file = open("values.txt")
    data = json.load(file)
    all_data = {}

    for i in data["Values"]:
        all_data.update(i)

    return all_data


# assignment of communication
# and data types dictionaries
values = load_values_file()
commtypes = values.get("commtype")
datatypes = values.get("datatype")


# class that contains all necessary functions when creating a packet
class PacketCreator:

    # function that creates any desired packet
    @staticmethod
    def create_packet(packet_data):
        HEADER_WITHOUT_CHECKSUM = b""
        CHECKSUM = b""
        DATA = b""

        if PacketCreator.commtype_to_bytes(packet_data.commtype):
            HEADER_WITHOUT_CHECKSUM += PacketCreator.commtype_to_bytes(packet_data.commtype)
        else:
            print("[PC] The communication type was not recognized")
            return

        if PacketCreator.datatype_to_bytes(packet_data.datatype):
            HEADER_WITHOUT_CHECKSUM += PacketCreator.datatype_to_bytes(packet_data.datatype)
        else:
            print("[PC] The data type was not recognized")
            return

        if type(packet_data.fragnum) == int and 0 < packet_data.fragnum < 2147483647:
            HEADER_WITHOUT_CHECKSUM += packet_data.fragnum.to_bytes(4, "big")
        else:
            print("[PC] The fragment number was not recognized")
            return

        if type(packet_data.fragtotal) == int and 0 < packet_data.fragtotal < 2147483647:
            HEADER_WITHOUT_CHECKSUM += packet_data.fragtotal.to_bytes(4, "big")
        else:
            print("[PC] The total number of fragments was not recognized")

        if type(packet_data.data) == bytes:
            DATA += packet_data.data
        else:
            DATA += str(packet_data.data).encode()

        CHECKSUM += crc32(HEADER_WITHOUT_CHECKSUM + DATA).to_bytes(4, "big")

        HEADER = HEADER_WITHOUT_CHECKSUM + CHECKSUM

        PACKET = HEADER + DATA
        return PACKET

    # function that gets the communication type
    # from the commtype dictionary
    @staticmethod
    def commtype_to_bytes(commtype):
        if commtype in commtypes:
            return commtypes.get(commtype).encode()
        else:
            return None

    # function that gets the data type
    # from the datatype dictionary
    @staticmethod
    def datatype_to_bytes(datatype):
        if datatype in datatypes:
            return datatypes.get(datatype).encode()
        else:
            return None

    # function that converts a number
    # to its bytes representation
    @staticmethod
    def create_bytes(number, size):
        return number.to_bytes(size, "big")
