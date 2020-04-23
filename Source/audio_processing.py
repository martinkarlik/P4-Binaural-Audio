import numpy as np
from scipy.signal import *
import sounddevice as sd
import librosa


def add_reverb(input_signal, sampling_freq, audio_data):
    if audio_data["reverb"] == "anechoic":
        return input_signal
    else:
        if audio_data["reverb"] == "forest":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/forrest.wav', sr=sampling_freq)
        elif audio_data["reverb"] == "church":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=sampling_freq)
        elif audio_data["reverb"] == "cave":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/cave.wav', sr=sampling_freq)

        input_signal = np.reshape(input_signal, (-1, 1))
        # print("tansposed input: ", input_signal.shape)
        reverb_impulse = np.reshape(reverb_impulse, (-1, 1))
        # print("Reverb impulse: ", reverb_impulse.shape)
        output = fftconvolve(input_signal, reverb_impulse, mode="full")
        output = np.append(output, output, axis=1)
        print("output signal: ", output.shape)
        sd.play(output)
        print("playing")
        sd.wait()
        return output
