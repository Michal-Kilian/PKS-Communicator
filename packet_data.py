# data class to store the information of a packet
class PacketData:
    commtype: str
    datatype: str
    fragnum: int
    fragtotal: int
    checksum: int
    data: bytes

    def __init__(self, commtype, datatype, fragnum, fragtotal, data):
        self.commtype = commtype
        self.datatype = datatype
        self.fragnum = fragnum
        self.fragtotal = fragtotal
        self.data = data

    def print(self):
        print("Commtype:", self.commtype, "Datatype:", self.datatype, "Fragnum:", self.fragnum,
              "Fragtotal:", self.fragtotal, "Data:", self.data)
