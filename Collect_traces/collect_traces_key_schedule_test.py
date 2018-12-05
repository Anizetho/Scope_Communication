import time
import pyvisa
import numpy as np



# Connect to Oscilloscope and some configurations
rm = pyvisa.ResourceManager()
print(rm.list_resources())

scope = rm.open_resource("USB::0x0699::0x03A3::C010163::INSTR")
scope.timeout = 20000

print scope.query("*IDN?")
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
scope.write("CH4:SCAle 100.000E-3") # Set the vertical scale for CH4
scope.write("CH4:BANdwidth FULl")   # Use full bandwidth of the oscilloscope

#
scope.write("DATA:SOU CH4") # Set the channel 4 like location of the waveform data transferred from the oscilloscope
scope.write('DATA:WIDTH 2') # Set 16 bits per data point in the waveform transferred
scope.write('DATA:ENC SRI') # Set ASCII like the format of outgoing waveform data.

scope.write('DATa:START 49950') # Specify first data point in the waveform record
scope.write('DATa:STOP 50200')  # Specify ending data point in the waveform record


############### Import key ##################

Nth_measurement = 10
with open('../Data/Key_Schedule_Measurements/Measurement_' + str(Nth_measurement) + '/key.txt') as f:
    key_hex = f.readlines()

key_hex = [x.strip() for x in key_hex]  # remove \n at the end
nb_keys = len(key_hex)
n_traces = nb_keys
key_string = [''] * nb_keys

i = 0
for x in key_hex:
    key_string[i] = x.decode("hex")
    i = i + 1
print("Key imported")

############## SEND DATA TO FPGA AND COLLECT TRACES #################

traces = [''] * n_traces
ciphertext = [''] * n_traces
test='2'

# To capture traces
i = 0
while i < nb_keys:
    ciphertext[i] = test.encode('hex')
    # scope.write('CURVE?')
    # traces[i] = scope.read_raw()
    traces[i] = scope.query_binary_values('CURVE?', datatype='h') # Transfers waveform data from oscilloscope in binary format
    print str(i) + "/" + str(n_traces - 1) + "  Capturing Traces ..."
    i = i + 1

# To save traces in a file
with open('../Data/Key_Schedule_Measurements/Measurement_' + str(Nth_measurement) + '/traces.txt', "wb") as f:
    for x in traces:
        for y in x:
            f.write(str(y))
            f.write(', ')
        f.write('\n')

# To save ciphertext in a file
with open('../Data/Key_Schedule_Measurements/Measurement_' + str(Nth_measurement) + '/ciphertext.txt', "wb") as f:
    for y in ciphertext:
        f.write(str(y))
        f.write('\n')

# To save parameters of scope in a file
with open('../Data/Key_Schedule_Measurements/Measurement_' + str(Nth_measurement) + '/scope_parameters.txt', "wb") as f:
    # WFMPRE specify the record length of the reference waveform
    f.write("Trigger Level  : ")
    f.write(scope.query("TRIGger:A:LEVel?"))
    f.write('\n')
    f.write("Trigger Mode   : ")
    f.write(scope.query("TRIGGER:A:MODE?"))
    f.write('\n')
    f.write("Trigger CH     : ")
    f.write(scope.query(":TRIGger:A:EDGE:SOUrce?"))
    f.write('\n')
    f.write("Horiz Scale    : ")
    f.write(scope.query("HORizontal:SCAle?"))
    f.write('\n')
    f.write("Horiz Pos      : ")
    f.write(scope.query("HORizontal:DELay:TIMe?"))
    f.write('\n')
    f.write("Vert Pos CH1   : ")
    f.write(scope.query("CH1:POSition?"))
    f.write('\n')
    f.write("Vert Pos CH4   : ")
    f.write(scope.query("CH4:POSition?"))
    f.write('\n')
    f.write("Vert Scale CH4 : ")
    f.write(scope.query("CH4:SCAle?"))
    f.write('\n')
    f.write("BW CH4         : ")
    f.write(scope.query("CH4:BANdwidth?"))
    f.write('\n')
    f.write("YMULT          : ")
    f.write(scope.query('WFMPRE:YMULT?'))
    f.write('\n')
    f.write("YZERO          : ")
    f.write(scope.query('WFMPRE:YZERO?'))
    f.write('\n')
    f.write("YOFF           : ")
    f.write(scope.query('WFMPRE:YOFF?'))
    f.write('\n')