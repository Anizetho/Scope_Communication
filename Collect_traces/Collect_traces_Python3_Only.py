# coding: utf-8

import time
import numpy as np
import subprocess
import PicoScope5244D as ps
from subprocess import Popen, PIPE
import sys
import matplotlib.pyplot as plt
import ftd2xx
import pyvisa
import codecs

#################################################################################
############# Connect to FT2232H and Configure it to 245 Sync Fifo ##############
#################################################################################
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


#################################################################################
############################ Configuration Picoscope ############################
#################################################################################

pico = ps.PicoScope()
pico.setResolution(resolution='12bit')
pico.setChannel(channel='A',coupling_type='AC',voltage_range='100mV',probe=1) # Mesures
#pico.setChannel(channel='B',coupling_type='DC',voltage_range='500mV',probe=1) # Trigger
pico.disableChannel(channel='B')

pico.setSimpleTrigger(channel='ext',threshold_mV=40,direction='rising',delay_samples=300,timeout_ms=3000) #300
pico.setSamplingParameters(preTrigger_ns=0,postTrigger_ns=1450,timebase=1) #800
print("Picoscope configured")
print(pico.getSamplingParameters())

#################################################################################
################################ Load info files ################################
#################################################################################

# To know the file's name ('Nth_measurement') to collect traces
with open('../../Data/AES_256/FileForName.txt') as f:
    Nth_measurement = f.readlines();
    Nth_measurement = [x.strip() for x in Nth_measurement]  # remove \n at the end
    Nth_measurement = Nth_measurement[0]

# To know the number of traces ('n_traces')
with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'\pt_fpga.txt') as f:
    plaintexts = f.readlines()
    plaintexts = [x.strip() for x in plaintexts] # remove \n at the end
    nb_plaintexts  = len(plaintexts)
    n_traces  = nb_plaintexts

# Functions to code and decode hex
encode_hex = codecs.getencoder("hex_codec")
decode_hex = codecs.getdecoder("hex_codec")

############# AES 256 INPUTS ###############
############### Import key ##################
with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'\keys_unique.txt') as f:
    key_hex = f.readlines()
key_header_hex_msb = '00' + key_hex[0][0:32]
key_header_hex_lsb ='01' + key_hex[0][32:64]
key_string = decode_hex(key_header_hex_msb)[0] + decode_hex(key_header_hex_lsb)[0]
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
    pt_string[i] = decode_hex(x)[0]
    i = i + 1
# pt_string représente les pltxts en hexa.
# pt_string commence par 03 pour être reconnu comme pltxt.


#################################################################################
################################ Collect traces #################################
#################################################################################

#print("Send first key ", key_string, " : ", h.write(key_string))
#print("Send first pltxt ", pt_string[0], " : ", h.write(pt_string[0]))
#print("First result : ", encode_hex(h.read(16))[0].decode('utf-8'))
h.write(key_string)
h.write(pt_string[0])
encode_hex(h.read(16))[0].decode('utf-8')

ciphertext = ['']*n_traces
trace_A = ['']*n_traces
pico.run()
i=0
print("Starting...")
while i < n_traces:

    # Delay to stabilize the channels
    if i==0:
        print('Waiting stabilization of picoscope...')
        time.sleep(10)

    # Send and retrieve data
    h.write(pt_string[i])
    ciphertext[i] = encode_hex(h.read(16))[0].decode('utf-8')
    pico.waitForTrigger()
    trace_A[i] = pico.getChannelValues('A')

    # Save info of time
    if i == 1:
        samplingParameters = pico.getSamplingParameters()
        noSamples = samplingParameters['noSamples']
        samplingPeriod_ns = samplingParameters['samplingPeriod_ns']
        timeVector = np.linspace(0, noSamples * samplingPeriod_ns, noSamples)
        with open('../../Data/AES_256/Measurement_' + str(Nth_measurement) + '/time.txt', "wt") as f:
            for x in timeVector:
                f.write(str(x) + ' ')
            f.write('\n')

    print(str(i + 1) + "/" + str(n_traces) + "  Capturing Traces ...")
    i = i + 1

    pico.run()

    # Save traces in file
    if i == 1000:
        with open('../../Data/AES_256/Measurement_' + str(Nth_measurement) + '/traces.txt', "wt") as f:
            for x in trace_A:
                for elem in x:
                    f.write(str(elem) + ' ')
                f.write('\n')
    if i == n_traces:
        with open('../../Data/AES_256/Measurement_' + str(Nth_measurement) + '/traces.txt', "wt") as f:
            for x in trace_A:
                for elem in x:
                    f.write(str(elem) + ' ')
                f.write('\n')


pico.stop()
print("Success")