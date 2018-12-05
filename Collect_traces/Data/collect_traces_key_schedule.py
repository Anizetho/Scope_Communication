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

# Connect to Oscilloscope and some configurations
rm = pyvisa.ResourceManager()
print(rm.list_resources())

scope = rm.open_resource("USB::0x0699::0x03A3::C010163::INSTR")
scope.timeout = 20000

print scope.query("*IDN?")
# Configure Trigger
scope.write("TRIGger:A:LEVel 1.2500E+00") # Set trigger level to 1.25V
scope.write("TRIGGER:A:MODE NORMAL")  # Set trigger to normal mode
scope.write(":TRIGger:A:EDGE:SOUrce CH1") # Trigger on CH2

# Configure Horizontal Parameters
scope.write("HORizontal:SCAle 100.0000E-9") #400/200/100
scope.write("HORizontal:DELay:TIMe 0.700E-6") #1.6000E-6/1.00/0.0

# Configure Vertical Parameters
scope.write("CH1:POSition 0.0") # 
scope.write("CH4:POSition 0.0") # 
scope.write("CH4:SCAle 100.000E-3")
# Use full bandwidth of the oscilloscope
scope.write("CH4:BANdwidth FULl") 
# scope.write("CH4:BANdwidth TWEnty") 

print 'Trigger Level  : ' + scope.query("TRIGger:A:LEVel?")
print 'Trigger Mode   : ' + scope.query("TRIGGER:A:MODE?")
print 'Trigger CH     : ' + scope.query(":TRIGger:A:EDGE:SOUrce?")
print 'Horiz Scale    : ' + scope.query("HORizontal:SCAle?")
print 'Horiz Pos      : ' + scope.query("HORizontal:DELay:TIMe?")
print 'Vert Pos CH1   : ' + scope.query("CH1:POSition?")
print 'Vert Pos CH4   : ' + scope.query("CH4:POSition?")
print 'Vert Scale CH4 : ' + scope.query("CH4:SCAle?")
print 'BW CH4         : ' + scope.query("CH4:BANdwidth?")

scope.write("DATA:SOU CH4")
scope.write('DATA:WIDTH 2')
scope.write('DATA:ENC SRI') #SRI

scope.write('DATa:START 49950')
scope.write('DATa:STOP 50200')

# scope.write('DATa:START 49200')
# scope.write('DATa:STOP 50000')


############### Import key ##################

Nth_measurement = '2003cr'
with open('..\Data\Key_Schedule_Measurements\Measurement_' + str(Nth_measurement) + '\key.txt') as f:
    key_hex = f.readlines()

key_hex = [x.strip() for x in key_hex] # remove \n at the end
nb_keys = len(key_hex)
n_traces = nb_keys
key_string = ['']*nb_keys

i=0
for x in key_hex:
	key_string[i] = x.decode("hex")
	i = i + 1
############## SEND DATA TO FPGA AND COLLECT TRACES #################
traces = ['']*n_traces

print h.write(key_string[0])
print h.read(16).encode('hex')
ciphertext = ['']*n_traces

i=0
while i < nb_keys:
	h.write(key_string[i])
	ciphertext[i] = h.read(16).encode('hex')
	# scope.write('CURVE?')
	# traces[i] = scope.read_raw()
	traces[i] = scope.query_binary_values('CURVE?', datatype='h')
	print str(i) + "/" + str(n_traces-1) + "  Capturing Traces ..."
	i = i + 1

# if i%1000==0:
with open('../Data/Key_Schedule_Measurements/Measurement_'+str(Nth_measurement)+'/traces.txt', "wb") as f :
	for x in traces:
		for y in x:
			f.write(str(y))
			f.write(', ')
		f.write('\n')
with open('../Data/Key_Schedule_Measurements/Measurement_'+str(Nth_measurement)+'/ciphertext.txt', "wb") as f :
	for y in ciphertext:
		f.write(str(y))
		f.write('\n')
				
with open('../Data/Key_Schedule_Measurements/Measurement_'+str(Nth_measurement)+'/scope_parameters.txt', "wb") as f :
	f.write(scope.query('WFMPRE:YMULT?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YZERO?'))
	f.write('\n')
	f.write(scope.query('WFMPRE:YOFF?'))
	f.write('\n')

# print "YMult : " + scope.query('WFMPRE:YMULT?')
# print "YZero : " + scope.query('WFMPRE:YZERO?')
# print "YOff : " + scope.query('WFMPRE:YOFF?')
# print "XIncr : " + scope.query('WFMPRE:XINCR?')