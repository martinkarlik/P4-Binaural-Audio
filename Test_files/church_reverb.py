import numpy as np
from scipy.signal import *
import sounddevice as sd
import soundfile as sf
import matplotlib.pyplot as plt
import librosa

guitar_signal, _ = sf.read('../Dependencies/Audio/guitar.wav')

# church
signal, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=44100)  # Downsample 94kHz to 44kHz

# forrest
# signal, sampling_freq = librosa.load('../Dependencies/Audio/forrest.wav', sr=44100)

# cave
# signal, sampling_freq = librosa.load('../Dependencies/Audio/cave.wav', sr=44100)

guitar_signal = np.reshape(guitar_signal, (-1, 1))
signal = np.reshape(signal, (-1, 1))

print(signal.shape)

# time_vector = np.arange(signal.shape[0])
# plt.figure(figsize=(15, 5))
# plt.title("Output")
# legend = ["impulse"]
# plt.plot(time_vector, signal[:, 0])
# plt.legend(legend)
# plt.show()

output = fftconvolve(guitar_signal, signal, mode="full")
# output = lfilter((signal[0:30000, 0]), 1, guitar_signal.transpose())
output = np.append(output.transpose(), output.transpose(), axis=1)
print(output.transpose().shape)

sd.play(output.transpose(), sampling_freq)
print("playing")
sd.wait()

