from pypico.v01 import PicoScope5244D as ps
import matplotlib.pyplot as plt
import numpy as np

# if the resolution is set on 12 bits, the following timebases apply
#   1: 500MS/s (if only one channel is enabled)
#   2: 250MS/s
#   3: 125MS/s
#   4: 62.5MS/s

pico = ps.PicoScope()
pico.setResolution(resolution='12bit')
pico.setChannel(channel='A',coupling_type='AC',voltage_range='5V',probe=10)
# pico.setChannel(channel='B',coupling_type='AC',voltage_range='2V',probe=1)
pico.disableChannel(channel='B')
pico.setSimpleTrigger(channel='ext',threshold_mV=300,direction='rising',delay_samples=0,timeout_ms=5000)
pico.setSamplingParameters(preTrigger_ns=1e5,postTrigger_ns=1e6,timebase=3)
# pico.setSamplingParameters(preTrigger_ns=100,postTrigger_ns=1000,samplingFrequency_kHz=100)
pico.run()
pico.waitForTrigger()

trace_A = pico.getChannelValues('A')
# trace_B = pico.getChannelValues('B')

samplingParameters = pico.getSamplingParameters()
noSamples = samplingParameters['noSamples']
samplingPeriod_ns = samplingParameters['samplingPeriod_ns']

time = np.linspace(0, noSamples*samplingPeriod_ns, noSamples)
plt.plot(time,trace_A)
# plt.plot(time,trace_B)
plt.show()

pico.stop()

print('-----------------')
print(pico.getStatus())
print(pico.getResolution())
print(pico.getChannelInfo('A'))
print(pico.getChannelInfo('B'))
print(pico.getTriggerInfo())
print(pico.getSamplingParameters())
