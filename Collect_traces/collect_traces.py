# coding: utf-8

import ftd2xx
import time
import pyvisa
import numpy as np


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

# Connect to Oscilloscope and some configurations
rm = pyvisa.ResourceManager()
print(rm.list_resources())

scope = rm.open_resource("USB::0x0699::0x03A3::C010163::INSTR")
scope.timeout = 20000
# Configure Trigger
scope.write("TRIGger:A:LEVel 1.2500E+00")       # Set trigger level to 1.25V
scope.write("TRIGGER:A:MODE NORMAL")            # Set trigger to normal mode
scope.write(":TRIGger:A:EDGE:SOUrce CH1")       # Trigger on CH1

# Configure Horizontal Parameters
scope.write("HORizontal:SCAle 100.0000E-9")     # Set the time base horizontal scale : 400/200/100
scope.write("HORizontal:DELay:TIMe 0.700E-6")   # Set the horizontal delay time. Horizontal Delay is the time between Time Zero and the first sample point.

# Configure Vertical Parameters
scope.write("CH1:POSition 0.0")     # Set the vertical position of the reference waveform (CH1)
scope.write("CH4:POSition 0.0")     # Set the vertical position of the reference waveform (CH4)
scope.write("CH4:SCAle 200.000E-3") # Set the vertical scale for CH4
scope.write("CH4:BANdwidth FULl")   # Use full bandwidth of the oscilloscope

#
scope.write("DATA:SOU CH4")   # Set the channel 4 like location of the waveform data transferred from the oscilloscope
scope.write('DATA:WIDTH 2')   # Set 16 bits per data point in the waveform transferred
scope.write('DATA:ENC ASCIi') # Set ASCII like the format of outgoing waveform data.

scope.write('DATa:START 49700') # Specify first data point in the waveform record
scope.write('DATa:STOP 50400')  # Specify ending data point in the waveform record

print("Oscilloscope configured")

############# AES 256 INPUTS ###############
############# Import correct file ###############
with open('../../Data/AES_256/FileForName.txt') as f:
	Nth_measurement = f.readlines();
	Nth_measurement = [x.strip() for x in Nth_measurement]  # remove \n at the end
	Nth_measurement = Nth_measurement[0]

############### Import key ##################
with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'\keys_unique.txt') as f:
    key_hex = f.readlines()
key_header_hex_msb = '00' + key_hex[0][0:32]
key_header_hex_lsb ='01' + key_hex[0][32:64]
key_string = key_header_hex_msb.decode("hex") + key_header_hex_lsb.decode("hex")
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
	pt_string[i] = x.decode("hex")
	i = i + 1
# pt_string représente les pltxts en hexa.
# pt_string commence par 03 pour être reconnu comme pltxt.


############## SEND DATA TO FPGA AND COLLECT TRACES #################
data = np.zeros((n_traces,1))
traces = ['']*n_traces

print("Send first key ", key_string, " : ", h.write(key_string))
print("Send first pltxt ", pt_string[0], " : ", h.write(pt_string[0]))
print("First result : ", h.read(16).encode('hex'))
ciphertext = ['']*n_traces

print("Starting...")
i=0
while i < n_traces:
	h.write(pt_string[i])
	ciphertext[i] = h.read(16).encode('hex')
	scope.write('CURVE?')
	traces[i] = scope.read_raw()
	# traces[n_mean*i+j] = scope.query_binary_values('CURV?', datatype='d', is_big_endian=True)
	print str(i) + "/" + str(n_traces-1) + "  Capturing Traces ..."
	i = i + 1
	if i%1000==0:
		with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/traces.txt', "wb") as f :
			for x in traces:
				f.write(str(x))
		with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/ciphertext.txt', "wb") as f :
			for y in ciphertext:
				f.write(str(y))
				f.write('\n')

with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/scope_parameters.txt', "wb") as f :
	f.write("Trigger Level                       : ")
	f.write(scope.query("TRIGger:A:LEVel?"))
	f.write('\n')
	f.write("Trigger Mode                        : ")
	f.write(scope.query("TRIGGER:A:MODE?"))
	f.write('\n')
	f.write("Trigger CH                          : ")
	f.write(scope.query(":TRIGger:A:EDGE:SOUrce?"))
	f.write('\n')
	f.write("Horiz Scale    (en V)               : ")
	f.write(scope.query("HORizontal:SCAle?"))
	f.write('\n')
	f.write("Horiz Pos                           : ")
	f.write(scope.query("HORizontal:DELay:TIMe?"))
	f.write('\n')
	f.write("Vert Scale CH1 (en V)               : ")
	f.write(scope.query("CH1:SCAle?"))
	f.write('\n')
	f.write("Vert Scale CH4 (en V)               : ")
	f.write(scope.query("CH4:SCAle?"))
	f.write('\n')
	f.write("Vert Pos CH1   (décalage par ligne) : ")
	f.write(scope.query("CH1:POSition?"))
	f.write('\n')
	f.write("Vert Pos CH4   (décalage par ligne) : ")
	f.write(scope.query("CH4:POSition?"))
	f.write('\n')
	f.write("BW CH4                              : ")
	f.write(scope.query("CH4:BANdwidth?"))
	f.write('\n')
	f.write("YMULT                               : ")
	f.write(scope.query('WFMPRE:YMULT?'))
	f.write('\n')
	f.write("YZERO                               : ")
	f.write(scope.query('WFMPRE:YZERO?'))
	f.write('\n')
	f.write("YOFF                                : ")
	f.write(scope.query('WFMPRE:YOFF?'))
	f.write('\n')

print("Success")
