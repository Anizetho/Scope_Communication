import ftd2xx
import time
import codecs

############# DEVICE CONFIGURATION #############
d = ftd2xx.listDevices() 					# list devices by serial, returns tuple of attached devices serial strings
h = ftd2xx.openEx(d[0])
h.setBitMode(0xFF, 0x00) 				# reset mode
time.sleep(0.01)
h.setBitMode(0xFF, 0x40)				# 245 fifo mode 
h.setLatencyTimer(2)
# h.setUSBParameters(0x10000,0x10000)
h.setFlowControl(0x0100, 0x0, 0x0)		# Avoid packet losses
h.setTimeouts(200,200)					# set RX/TX timeouts
h.purge(1)								#Purge RX Buffer
h.purge(2)								#Purge TX Buffer
time.sleep(2)

############# HEADER DEFINITION ################
header_1 = "00" # Header MSB Key
header_2 = "01" # Header LSB Key
header_3 = "02" # Header MSB Mask
header_4 = "03" # Header LSB Mask
header_5 = "04" # Header plaintext "03" Encryption mode - "0B" Decryption mode

############# AES 256 CBC INPUTS ###############
key_hex_1 = "000102030405060708090a0b0c0d0e0f"
key_hex_2 = "101112131415161718191a1b1c1d1e1f"
mask_hex_1 ="102030405060708090A0B0C0D0E0F101"
mask_hex_2 = "112131415161718191A1B1C1D1E1F101"
pt_hex = "00112233445566778899aabbccddeeff"

key_header_hex_1 = header_1 + key_hex_1
key_header_hex_2 = header_2 + key_hex_2
mask_header_hex_1 = header_3 + mask_hex_1
mask_header_hex_2 = header_4 + mask_hex_2
# pt_header_hex = header_5 + pt_hex       # Si faking implémentée
pt_header_hex = header_4 + pt_hex         # Si faking non implémentée

decode_hex = codecs.getdecoder("hex_codec")
encode_hex = codecs.getencoder("hex_codec")
mask_string = decode_hex(mask_header_hex_1)[0] + decode_hex(mask_header_hex_2)[0]
key_string = decode_hex(key_header_hex_1)[0] + decode_hex(key_header_hex_2)[0]
pt_string_1 = decode_hex(pt_header_hex)[0]
#key_string = key_header_hex_1.decode("hex") + key_header_hex_2.decode("hex")
#pt_string_1 = pt_header_hex.decode("hex")

nb_plaintexts = 1000;

############# SEND DATA TO FPGA #################
i=0
rec_sorted = ""
#print(h.write(mask_string))
print(h.write(key_string))
print(h.write(pt_string_1))
print(encode_hex(h.read(16))[0].decode('utf-8'))
#print(h.read(16).encode('hex'))
while i < nb_plaintexts:
    h.write(pt_string_1)
    rec = encode_hex(h.read(16))[0].decode('utf-8')
    #rec = h.read(16).encode('hex')
    rec_sorted = rec_sorted + rec + "\n"
    i = i + 1
    #print(i)
with open("..\cipher_test.txt", "w") as f :
    f.write(rec_sorted)
h.close()