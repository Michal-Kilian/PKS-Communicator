import json
from indexes import header_start, header_end, commtype_start, commtype_end, datatype_start, datatype_end, \
    fragnum_start, fragnum_end, fragtotal_start, fragtotal_end, checksum_start, checksum_end, data_start
from packet_data import PacketData


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
# and data types bytes dictionaries
values = load_values_file()
commtype_bytes_dict = values.get("commtype_bytes")
datatype_bytes_dict = values.get("datatype_bytes")


# class that contains all necessary functions when translating a packet
class PacketTranslator:

    # function that translates a packet to a PacketData instance
    @staticmethod
    def translate_packet(packet):
        HEADER = packet[header_start: header_end]
        DATA = packet[data_start:]

        commtype_bytes = HEADER[commtype_start: commtype_end]
        datatype_bytes = HEADER[datatype_start: datatype_end]
        fragnum_bytes = HEADER[fragnum_start: fragnum_end]
        fragtotal_bytes = HEADER[fragtotal_start: fragtotal_end]
        checksum_bytes = HEADER[checksum_start: checksum_end]

        commtype = PacketTranslator.get_commtype(commtype_bytes)
        datatype = PacketTranslator.get_datatype(datatype_bytes)

        fragnum = int.from_bytes(fragnum_bytes, "big")
        fragtotal = int.from_bytes(fragtotal_bytes, "big")
        checksum = int.from_bytes(checksum_bytes, "big")

        return PacketData(commtype, datatype, fragnum, fragtotal, DATA), checksum

    # function that gets the communication type
    # bytes from the commtype bytes dictionary
    @staticmethod
    def get_commtype(commtype_bytes):
        if commtype_bytes.decode() in commtype_bytes_dict:
            return commtype_bytes_dict.get(commtype_bytes.decode())
        else:
            print("[PT] The communication type in this packet was not recognized")
            return None

    # function that gets the data type
    # bytes from the datatype bytes dictionary
    @staticmethod
    def get_datatype(datatype_bytes):
        if datatype_bytes.decode() in datatype_bytes_dict:
            return datatype_bytes_dict.get(datatype_bytes.decode())
        else:
            print("[PT] The data type in this packet was not recognized")
            return None
