# coding: utf-8

import time
import numpy as np
import subprocess
import PicoScope5244D as ps
import matplotlib.pyplot as plt

#################################################################################
############################ Configuration Picoscope ############################
#################################################################################

pico = ps.PicoScope()
pico.setResolution(resolution='8bit')
pico.setChannel(channel='A',coupling_type='DC',voltage_range='100mV',probe=1) # Mesures
pico.setChannel(channel='B',coupling_type='DC',voltage_range='500mV',probe=1)  # Trigger
pico.setSimpleTrigger(channel='B',threshold_mV=20,direction='rising',delay_samples=0,timeout_ms=5000)
pico.setSamplingParameters(preTrigger_ns=10,postTrigger_ns=1000)
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
	with open('../../Data/AES_256/Condition_9000' + '.txt', "w") as f:
		f.write(str(i))


	### Call Python 2 ###
	process = subprocess.Popen(python2_command.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()
	if i == 0:
		with open('../../Data/AES_256/Python2Files' + '.txt', "w") as f:
			f.write(str(output))
		with open('../../Data/AES_256/Python2Files' + '.txt', "r") as f:
			outputFile = f.readlines()
			for elem in outputFile:
				print(elem[2:19])  # FTDX
				print(elem[21:45]) # FilesPython2
		print("Starting...")


	### Python 3 : capture and save data scope ###
	trace_A[i] = pico.getChannelValues('A')

	# Delay to stabilize the channels
	if i==0:
		time.sleep(25)

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

	print(str(i) + "/" + str(9000-1) + "  Capturing Traces ...")
	i = i + 1

	# Save traces in file
	if i % 1000 == 0:
		with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/traces.txt', "wt") as f:
			for x in trace_A:
				for elem in x:
					f.write(str(elem) + ' ')
				f.write('\n')

#################################################################################
################################ Save parameters ################################
#################################################################################

with open('../../Data/AES_256/Measurement_'+str(Nth_measurement)+'/scope_parameters.txt', "wb") as f :
	f.write("Status                              : ")
	f.write(pico.getStatus())
	f.write('\n')
	f.write("Resolution                          : ")
	f.write(pico.getResolution())
	f.write('\n')
	f.write("Info Channel A                      : ")
	f.write(pico.getChannelInfo('A'))
	f.write('\n')
	f.write("Info Channel B                      : ")
	f.write(pico.getChannelInfo('B'))
	f.write('\n')
	f.write("Info trigger                        : ")
	f.write(pico.getTriggerInfo())
	f.write('\n')
	f.write("Info sampling parameters            : ")
	f.write(pico.getSamplingParameters())
	f.write('\n')

print("Success")