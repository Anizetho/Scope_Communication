# coding: utf-8

import ftd2xx
import time
import pyvisa
import numpy as np
import codecs


# Connect to FT2232H and Configure it to 245 Sync Fifo
d = ftd2xx.listDevices()
h = ftd2xx.openEx(d[0])
h.setBitMode(0xFF, 0x00) 				# reset mode
time.sleep(0.01)
h.setBitMode(0xFF, 0x40)				# 245 fifo mode
h.setLatencyTimer(2)
# h.setUSBParameters(0x10000,0x10000)
h.setFlowControl(0x0100, 0x0, 0x0)		# Avoid packet losses
h.setTimeouts(200,200)					# set RX/TX timeouts
h.purge(1)								#Purge RX Buffer
h.purge(2)
print("FT223H configured")


## Functions to code and decode hex
encode_hex = codecs.getencoder("hex_codec")
decode_hex = codecs.getdecoder("hex_codec")

############# AES 256 INPUTS ###############
############# Importe correct file ###############
with open('../../Data/AES_256/FileForName.txt') as f:
    Nth_measurement = f.readlines();
    Nth_measurement = [x.strip() for x in Nth_measurement]  # remove \n at the end
    Nth_measurement = Nth_measurement[0]

############### Import key ##################
with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'\keys_unique.txt') as f:
    key_hex = f.readlines()
key_header_hex_msb = '02' + key_hex[0][0:32]
key_header_hex_lsb ='03' + key_hex[0][32:64]
key_string = decode_hex(key_header_hex_msb)[0] + decode_hex(key_header_hex_lsb)[0]
# key_string = key_header_hex_msb.decode("hex") + key_header_hex_lsb.decode("hex")
# key_string représente la clé en hexa.
# key_string commence par 00 pour 16 premiers bytes
# key_string commence par 01 pour 16 derniers bytes

################ Import plaintexts #################
with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'\pt_fpga.txt') as f:
    plaintexts = f.readlines()
plaintexts = [x.strip() for x in plaintexts] # remove \n at the end
nb_plaintexts  = len(plaintexts)
n_traces  = nb_plaintexts

pt_string = ['']*nb_plaintexts
i=0
for x in plaintexts:
    #pt_string[i] = x.decode("hex")
    pt_string[i] = decode_hex(x)[0]
    i = i + 1
# pt_string représente les pltxts en hexa.
# pt_string commence par 03 pour être reconnu comme pltxt.


############## SEND DATA TO FPGA AND COLLECT TRACES #################
data = np.zeros((n_traces,1))
traces = ['']*n_traces

print("Send first key ", key_string, " : ", h.write(key_string))
print("Send first pltxt ", pt_string[0], " : ", h.write(pt_string[0]))
print("First result : ", encode_hex(h.read(16))[0].decode('utf-8'))
#print("First result : ", h.read(16).encode('hex'))

ciphertext = ['']*n_traces

print("Starting...")
i=0
while i < n_traces:
    h.write(pt_string[i])
    ciphertext[i] = encode_hex(h.read(16))[0].decode('utf-8')
    #ciphertext[i] = h.read(16).encode('hex')
    #scope.write('CURVE?')
    #traces[i] = scope.read_raw()
    # traces[n_mean*i+j] = scope.query_binary_values('CURV?', datatype='d', is_big_endian=True)
    print(str(i) + "/" + str(n_traces-1) + "  Capturing Traces ...")
    i = i + 1
    if i%1000==0:
        with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/traces.txt', "w") as f :
            for x in traces:
                f.write(str(x))
        with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/ciphertext.txt', "w") as f :
            for y in ciphertext:
                f.write(str(y))
                f.write('\n')


