import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wave
from scipy.signal import *
from scipy.special import comb


def plainReverberator(inputSignal, delay, filterParam):
    nData = np.size(inputSignal)
    outputSignal = np.zeros(nData)
    for n in np.arange(nData):
        if n < delay:
            outputSignal[n] = inputSignal[n]
        else:
            outputSignal[n] = inputSignal[n] + filterParam*outputSignal[n-delay]
    return outputSignal

def allpassReverberator(inputSignal, delay, apParameter):
    nData = np.size(inputSignal)
    outputSignal = np.zeros(nData)
    for n in np.arange(nData):
        if n < delay:
            outputSignal[n] = inputSignal[n]
        else:
            outputSignal[n] = apParameter*inputSignal[n] + inputSignal[n-delay] - \
                apParameter*outputSignal[n-delay]
    return outputSignal


def plainGainFromReverbTime(reverbTime, plainDelay, samplingFreq):
    nDelays = np.size(plainDelay)
    plainGains = np.zeros(nDelays)
    for ii in np.arange(nDelays):
        plainGains[ii] = 10**(-3*plainDelay[ii]/(reverbTime*samplingFreq))
    return plainGains


def shroederReverb(inputSignal, mixingParams, plainDelays, plainGains, allpassDelays, apParams):
    nData = np.size(inputSignal)
    tmpSignal = np.zeros(nData)
    # run the plain reverberators in parallel
    nPlainReverberators = np.size(plainDelays)
    for ii in np.arange(nPlainReverberators):
        tmpSignal = tmpSignal + \
            mixingParams[ii]*plainReverberator(inputSignal, plainDelays[ii], plainGains[ii])
    # run the allpass reverberators in series
    nAllpassReverberators = np.size(allpassDelays)
    for ii in np.arange(nAllpassReverberators):
        tmpSignal = allpassReverberator(tmpSignal, allpassDelays[ii], apParams[ii])
    return tmpSignal


# # recording
sampling_freq = 44100
sd.default.samplerate = sampling_freq
sd.default.channels = (1, 5)
rec_time = 5  # seconds

mic_data = sd.rec(rec_time * sampling_freq)

print("Recording...")
sd.wait()
print("Recording ended.")
print(mic_data)
# sampling_freq, guitarSignal = wave.read('D:\Github\P4_UnderConstruction\Project_A.B.B.A_2.0\guitar.wav')
# guitarSignal = guitarSignal/2**15 # normalise

mixingParams = np.array([0.3, 0.25, 0.25, 0,20])
plainDelays = np.array([1553, 1613, 1493, 1153])
allpassDelays = np.array([223, 443])
apParams = np.array([-0.7, -0.7])
reverbTime = 1.1 # seconds
plainGains = plainGainFromReverbTime(reverbTime, plainDelays, sampling_freq)
# compute the impulse response of the room
irLength = np.int(np.floor(reverbTime*sampling_freq))
impulse = np.r_[np.array([1]),np.zeros(irLength-1)]
impulseResponse = guitarSignalWithReverb = \
    shroederReverb(impulse, mixingParams, plainDelays, plainGains, allpassDelays, apParams)
guitarSignalWithReverb = \
    shroederReverb(mic_data, mixingParams, plainDelays, plainGains, allpassDelays, apParams)

sd.play(guitarSignalWithReverb)
sd.wait()
