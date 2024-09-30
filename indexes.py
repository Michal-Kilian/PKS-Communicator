# important indexes used
# when translating a packet
header_start = 0
header_end = 14

commtype_start = 0
commtype_end = 1

datatype_start = 1
datatype_end = 2

fragnum_start = 2
fragnum_end = 6

fragtotal_start = 6
fragtotal_end = 10

checksum_start = 10
checksum_end = 14

data_start = 14

header_length = 14

# important values used
# when receiving a packet
success_status_code = 200

error_status_code = 400

separator = "<<<>>>"

download_path = "downloads"
