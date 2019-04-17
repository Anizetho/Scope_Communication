# coding: utf-8

import time
import numpy as np
import subprocess
import PicoScope5244D as ps
from subprocess import Popen, PIPE
import sys
import matplotlib.pyplot as plt

#################################################################################
############################ Configuration Picoscope ############################
#################################################################################

pico = ps.PicoScope()
pico.setResolution(resolution='8bit')
pico.setChannel(channel='A',coupling_type='DC',voltage_range='100mV',probe=1) # Mesures
pico.setChannel(channel='B',coupling_type='DC',voltage_range='500mV',probe=1) # Trigger
pico.setSimpleTrigger(channel='B',threshold_mV=20,direction='rising',delay_samples=200,timeout_ms=0)
pico.setSamplingParameters(preTrigger_ns=0,postTrigger_ns=1200)
print("Picoscope configured")


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

print('Files of Python_3 loaded')


#################################################################################
################################ Collect traces #################################
#################################################################################

python2_command = 'C:\Python27\python.exe Python2.py arg1'
trace_A = ['']*n_traces
pico.run()
i=0
while i < n_traces:

    ### Write the condition for the python 2 script ###
    with open('../../Data/AES_256/Condition' + '.txt', "w") as f:
        f.write(str(i))

    # Delay to stabilize the channels
    if i==0:
        time.sleep(35)

    ### Call Python 2 ###
    with Popen(python2_command.split(), stdin=PIPE, stdout=PIPE) as proc:
        output, error = proc.communicate((i).to_bytes(3, sys.byteorder))
        #proc.wait()
        print(int.from_bytes(output, sys.byteorder))

        if i == 0:
            with open('../../Data/AES_256/Python2Files' + '.txt', "w") as f:
                f.write(str(output))
            with open('../../Data/AES_256/Python2Files' + '.txt', "r") as f:
                outputFile = f.readlines()
                for elem in outputFile:
                    print(elem[2:19])  # FTDX
                    print(elem[21:45]) # FilesPython2
            print("Starting...")
        #process = subprocess.Popen(python2_command.split(), stdout=subprocess.PIPE)
        #output, error = process.communicate()

    pico.waitForTrigger()

    ### Python 3 : capture and save data scope ###
    trace_A[i] = pico.getChannelValues('A')

    # Save info of time
    if i==1:
        samplingParameters = pico.getSamplingParameters()
        noSamples = samplingParameters['noSamples']
        samplingPeriod_ns = samplingParameters['samplingPeriod_ns']
        timeVector = np.linspace(0, noSamples * samplingPeriod_ns, noSamples)
        with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/time.txt', "wt") as f :
            for x in timeVector:
                f.write(str(x) + ' ')
            f.write('\n')

    pico.run()

    print(str(i+1) + "/" + str(n_traces) + "  Capturing Traces ...")
    i = i + 1

    # Save traces in file
    if i % 1000 == 0:
        with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/traces.txt', "wt") as f:
            for x in trace_A:
                for elem in x:
                    f.write(str(elem) + ' ')
                f.write('\n')

#################################################################################
########################### Save Picoscope parameters ###########################
#################################################################################

#with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/scope_parameters.txt', "wb") as f :
#	f.write("Status                              : ")
#	f.write(pico.getStatus())
#	f.write('\n')
#	f.write("Resolution                          : ")
#	f.write(pico.getResolution())
#	f.write('\n')
#	f.write("Info Channel A                      : ")
#	f.write(pico.getChannelInfo('A'))
#	f.write('\n')
#	f.write("Info Channel B                      : ")
#	f.write(pico.getChannelInfo('B'))
#	f.write('\n')
#	f.write("Info trigger                        : ")
#	f.write(pico.getTriggerInfo())
#	f.write('\n')
#	f.write("Info sampling parameters            : ")
#	f.write(pico.getSamplingParameters())
#	f.write('\n')

pico.stop()
print("Success")