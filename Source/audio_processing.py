import numpy as np
from scipy.signal import *
import sounddevice as sd
import librosa


# reverb_data = [dict(reverb_type="church"), 8000, dict(reverb_type="forest"), 8000]


def add_reverb(input_signal, sampling_freq, reverb_type):

    if reverb_type == "anechoic":
        return input_signal
    else:
        if reverb_type == "forest":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/forrest.wav', sr=sampling_freq)
        elif reverb_type == "church":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=sampling_freq)
        elif reverb_type == "cave":
            reverb_impulse, sampling_freq = librosa.load('../Dependencies/Audio/cave.wav', sr=sampling_freq)

        input_signal = np.reshape(input_signal, (-1, 1))
        print("tansposed input: ", input_signal.shape)
        reverb_impulse = np.reshape(reverb_impulse, (-1, 1))
        # print("Reverb impulse: ", reverb_impulse.shape)
        output = fftconvolve(input_signal, reverb_impulse, mode="same")
        output = np.append(output, output, axis=1)
        print("output signal: ", output.shape)
        # sd.play(output)
        # print("playing")
        # sd.wait()
        return output


def remove_redundant_reverb(data):
       
    output = []
    elapsed_duration = 0
    current_reverb = data[0][0]

    for i in np.arange(0, len(data)):

        if data[i][0] != current_reverb:
            output.append([current_reverb, elapsed_duration])
            elapsed_duration = 0
            current_reverb = data[i][0]

        elapsed_duration += data[i][1]

    output.append([current_reverb, elapsed_duration])

    return output
