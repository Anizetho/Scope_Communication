import visa
import time
import numpy as np

from datetime import datetime

rm = visa.ResourceManager()
print(rm.list_resources())

# Connect to Oscilloscope and some configurations
#scope = rm.open_resource("USB::0x0699::0x0368::C016375::INSTR")
scope = rm.open_resource("USB::0x0699::0x03A3::C010163::INSTR")
scope.timeout = 20000
scope.write("*IDN?")
print(scope.read())
scope.write("TRIGger:A:LEVel 1.2500E+00") # Set trigger level to 1.25V
print('Trigger Level : ' + scope.query("TRIGger:A:LEVel?"))
scope.write("TRIGGER:A:MODE NORMAL")  # Set trigger to normal mode
print('Trigger Mode : ' + scope.query("TRIGGER:A:MODE?"))
scope.write(":TRIGger:A:EDGE:SOUrce CH2") #Set channel to trigger
print('Channel to trigger : ' + scope.query(":TRIGger:A:EDGE:SOUrce?"))
scope.write("CH3:BANdwidth FULl") # Use full bandwidth of the oscilloscope
print('Bandwith Channel 3 : ' + scope.query("CH3:BANdwidth?"))
print('Length measure : ' + scope.query("HORizontal:ACQLENGTH?"))

scope.write("DATA:SOU CH3") # Sets the channel 3 like location of the waveform data transferred from the oscilloscope
scope.write('DATA:WIDTH 2') # Sets 16 bits per data point in the waveform transferred
scope.write('DATA:ENC ASCIi') # Sets ASCII like the format of outgoing waveform data.

# WFMPRE specify the record length of the reference waveform
print "YMult : " + scope.query('WFMPRE:YMULT?')
print "YZero : " + scope.query('WFMPRE:YZERO?')
print "YOff : " + scope.query('WFMPRE:YOFF?')
print "XIncr : " + scope.query('WFMPRE:XINCR?')

scope.write('DATa:START 50750'); # Specify first data point in the waveform record
print 'START : ' + scope.query('DATa:START?')
scope.write('DATa:STOP 52300'); # Specify ending data point in the waveform record
print 'STOP : ' + scope.query('DATa:STOP?')

import numpy as np

Nth_measurement = 10

############### Import key ##################

with open("../Data/Measurement_" + str(Nth_measurement) + "/key.txt", 'r') as f:
	key_hex = f.readlines()

key_header_hex_msb = '00' + key_hex[0][0:32]
key_header_hex_lsb = '01' + key_hex[0][32:64]
key_string = key_header_hex_msb.decode("hex") + key_header_hex_lsb.decode("hex")
print("Key imported")

################ Import plaintexts #################
with open('..\Data\Measurement_' + str(Nth_measurement) + '\pt_fpga.txt', 'r') as f:
	plaintexts = f.readlines()
plaintexts = [x.strip() for x in plaintexts]  # remove \n at the end
nb_plaintexts = len(plaintexts)
n_traces = nb_plaintexts
pt_string = [''] * nb_plaintexts

i = 0
for x in plaintexts:
	pt_string[i] = x.decode("hex")
	i = i + 1

print("Plaintexts imported")



###################################################

data = np.zeros((n_traces,1))
n_mean = 1
traces = ['']*n_traces*n_mean
ciphertext = ['']*n_traces*n_mean

test = "2"


i = 0
while i < n_traces:
	j = 0
	while j < n_mean:
		ciphertext[n_mean*i+j] = test.encode('hex')
		scope.write('CURVE?')
		traces[n_mean * i + j] = scope.read_raw()
		print str(i) + "/" + str(n_traces - 1) + "  Capturing Traces ..."
		j = j + 1
	i = i + 1
	if i % 1000 == 0:
		with open('../Data/Measurement_' + str(Nth_measurement) + '/traces.txt', "wb") as f:
			for x in traces:
				f.write(str(x))
		print("traces captured")
		with open('../Data/Measurement_' + str(Nth_measurement) + '/ciphertext.txt', "wb") as f:
			for y in ciphertext:
				f.write(str(y))
				f.write('\n')
		print("ciphertext captured")
with open('../Data/Measurement_' + str(Nth_measurement) + '/scope_parameters.txt', "wb") as f:
	f.write(scope.query('WFMPRE:YMULT?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YZERO?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YOFF?'))
	f.write('\n')

