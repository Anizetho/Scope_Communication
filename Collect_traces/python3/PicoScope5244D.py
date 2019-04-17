import ctypes, time
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
from picosdk.constants import PICO_STATUS

'''

Python wrapper for PicoScope 5244D (PicoSDK 10.6.13.58 64-bit)
Thales Belgium

version: 0.0 (Feb. 2019)
author: Francois Durvaux
mail: francois.durvaux@be.thalesgroup.com

'''

class PicoScope:

    chandle = ctypes.c_int16()
    status = {}
    channel_info = {
        'A': {'enabled': True},
        'B': {'enabled': True}
        }
    trigger_info = {}
    
    resolution = 0
    timebase = 0
    preTrigger_ns = 0
    postTrigger_ns = 0
    samplingPeriod_ns = 0
    samplingFrequency_kHz = 0
    preTrigger_samples = 0
    postTrigger_samples = 0
    noSamples = 0
    maxSamples = 0

    def __init__(self):
        self.openDevice()

    def openDevice(self):
        self.resolution = '8BIT'
        _resolution = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_' + self.resolution.upper()]
        self.status['openunit'] = ps.ps5000aOpenUnit(ctypes.byref(self.chandle), None, _resolution)
        try:
            assert_pico_ok(self.status['openunit'])
            return 0
        except:
            powerStatus = self.status["openunit"]
            if powerStatus == 286:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
            elif powerStatus == 282:
                self.status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
            else:
                # raise
                return -1

    def disableChannel(self,channel):
        _channel = ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + channel.upper()]
        self.status['set' + channel.upper()] = ps.ps5000aSetChannel(self.chandle, _channel, 0, 0, 0, 0)
        self.channel_info[channel.upper()] = {'enabled': False}
        assert_pico_ok(self.status['set' + channel.upper()])

    def getChannelInfo(self,channel):
        return self.channel_info[channel.upper()]

    def getChannelValues(self,channel):
        _channel = ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + channel.upper()]
        buf = (ctypes.c_int16 * self.noSamples)()
        self.status['setBuffer_' + channel.upper()] = ps.ps5000aSetDataBuffer(self.chandle, _channel, ctypes.byref(buf), self.noSamples, 0, 0)
        assert_pico_ok(self.status['setBuffer_' + channel.upper()])

        overflow = ctypes.c_int16()
        cnoSamples = ctypes.c_int32(self.noSamples)

        self.status['getChannelValues' + channel.upper()] = ps.ps5000aGetValues(self.chandle, 0, ctypes.byref(cnoSamples), 0, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(self.status['getChannelValues' + channel.upper()])

        maxADC = ctypes.c_int16()
        self.status['maximumValue'] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status['maximumValue'])
        _voltage_range = ps.PS5000A_RANGE['PS5000A_' + self.channel_info[channel.upper()]['voltage_range']]
        buf_mV =  adc2mV(buf, _voltage_range, maxADC)

        return buf_mV

    def getResolution(self):
        return self.resolution

    def getSamplingParameters(self):
        sampling_parameters = {
            'timebase': self.timebase,
            'preTrigger_ns': self.preTrigger_ns,
            'postTrigger_ns': self.postTrigger_ns,
            'samplingPeriod_ns': self.samplingPeriod_ns,
            'samplingFrequency_kHz': self.samplingFrequency_kHz,
            'preTrigger_samples': self.preTrigger_samples,
            'postTrigger_samples': self.postTrigger_samples,
            'noSamples': self.noSamples,
            'maxSamples': self.maxSamples
        }
        return sampling_parameters

    def getStatus(self):
        return self.status

    def getTriggerInfo(self):
        return self.trigger_info

    def isChannelEnabled(self,channel):
        return self.channel_info[channel.upper()]['enabled']

    def run(self):
        self.status['run'] = ps.ps5000aRunBlock(self.chandle, self.preTrigger_samples, self.postTrigger_samples, self.timebase, None, 0, None, None)
        assert_pico_ok(self.status['run'])

    def setChannel(self,channel,coupling_type,voltage_range,probe):
        _channel = ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + channel.upper()]
        _coupling_type = ps.PS5000A_COUPLING['PS5000A_' + coupling_type.upper()]
        _voltage_range = ps.PS5000A_RANGE['PS5000A_' + voltage_range.upper()]
        self.status['set' + channel.upper()] = ps.ps5000aSetChannel(self.chandle, _channel, 1, _coupling_type, _voltage_range, 0)
        assert_pico_ok(self.status['set' + channel.upper()])
        self.channel_info[channel.upper()].update({
            'coupling_type': coupling_type.upper(),
            'voltage_range': voltage_range.upper(),
            'probe': int(probe)
            })

    def setResolution(self,resolution):
        self.resolution = resolution.upper()
        _resolution = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_' + self.resolution.upper()]
        self.status['setRes'] = ps.ps5000aSetDeviceResolution(self.chandle, _resolution)
        assert_pico_ok(self.status['setRes'])

    def setSimpleTrigger(self,channel,threshold_mV,direction,delay_samples,timeout_ms=1000):
    # TODO: handling of external trigger
        maxADC = ctypes.c_int16()
        self.status['maximumValue'] = ps.ps5000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status['maximumValue'])
        _channel = ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + channel.upper()]
        _voltage_range = ps.PS5000A_RANGE['PS5000A_' + self.channel_info[channel]['voltage_range']]
        _threshold_ADC = int(mV2adc(threshold_mV, _voltage_range, maxADC))
        _direction = ps.PS5000A_THRESHOLD_DIRECTION['PS5000A_' + direction.upper()]
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.chandle, 1, _channel, _threshold_ADC, _direction, delay_samples, timeout_ms)
        assert_pico_ok(self.status["trigger"])
        self.trigger_info = {
            'channel': channel.upper(),
            'threshold_mV': threshold_mV,
            'direction': direction.upper(),
            'delay_samples': delay_samples}

    def setSamplingParameters(self,preTrigger_ns,postTrigger_ns,samplingFrequency_kHz=0):

        timeInterval_ns = ctypes.c_float()
        maxSamples = ctypes.c_int32()

        if(samplingFrequency_kHz==0):
            timebase_invalid = True
            while timebase_invalid:
                self.status['getTimebase2'] = ps.ps5000aGetTimebase2(self.chandle, self.timebase, 0, ctypes.byref(timeInterval_ns), ctypes.byref(maxSamples), 0)
                timebase_invalid = self.status['getTimebase2']==PICO_STATUS['PICO_INVALID_TIMEBASE']
                if timebase_invalid:
                    self.timebase +=1

        else:
            # TODO
            print('CUSTOM SAMPLING FREQUENCY NOT YET SUPPORTED')
            return -1

        self.preTrigger_ns = preTrigger_ns
        self.postTrigger_ns = postTrigger_ns
        self.maxSamples = maxSamples.value
        self.samplingPeriod_ns = timeInterval_ns.value
        self.samplingFrequency_kHz = 1/self.samplingPeriod_ns*10**6
        self.noSamples = round((self.preTrigger_ns+self.postTrigger_ns)/self.samplingPeriod_ns)
        self.preTrigger_samples = round(self.noSamples*self.preTrigger_ns/(self.preTrigger_ns+self.postTrigger_ns))
        self.postTrigger_samples = self.noSamples-self.preTrigger_samples

        if(self.noSamples>self.maxSamples):
            print('TOO MANY SAMPLES')
            return -1
        else:
            return 0

    def stop(self):
        self.status["stop"] = ps.ps5000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])
        self.status["close"]=ps.ps5000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

    def waitForTrigger(self):
        ready = ctypes.c_int16(0)
        while ready.value == 0:
            self.status['triggered'] = ps.ps5000aIsReady(self.chandle, ctypes.byref(ready))
        assert_pico_ok(self.status['triggered'])
