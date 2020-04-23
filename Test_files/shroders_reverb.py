from tkinter import *
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wave
from scipy.interpolate import interp1d


def delay():
    # load the sample file
    sd.stop()
    sampling_freq, guitar_signal = wave.read('../Dependencies/Audio/guitar.wav')
    guitar_signal = guitar_signal / 2 ** 15  # normalise

    # audio processing
    dry_wet = mix_variable.get()  # get the slider value for the dry/wet
    convert = interp1d([0, 100], [0, 1])  # remap the values from 0 to 100 to 0 to one for convenience sake
    converted_dry_wet = convert(dry_wet)  # store the remapped values in a variable
    desired_reverb_time = delay_variable.get()  # in milliseconds
    plain_gains = calculate_reverb_time(desired_reverb_time, plain_delay, sampling_freq)  # calculate the delay needed for x amount of millisecs
    wet_guitar_signal = shroeders_reverb(guitar_signal, mix_parameters, plain_delay, plain_gains, allpass_delay, allpass_filter_coefficients)  # get the wet guitar signal
    final_signal = (guitar_signal * ((converted_dry_wet - 1) * - 1)) + (wet_guitar_signal * converted_dry_wet) # add the wet and dry signals together with the mix parameters

    # play the sample file
    sd.play(final_signal)
    print("dry/wet: ", converted_dry_wet)
    print("delay in ms: ", desired_reverb_time)
    print("playing")


# Delays the signal
def plain_reverb(input_signal, filter_coefficient, delay):
    input_length = np.size(input_signal)
    output_signal = np.zeros(input_length)

    for n in np.arange(input_length):
        if n < delay:
            output_signal[n] = input_signal[n]
        else:
            output_signal[n] = input_signal[n] + filter_coefficient * output_signal[n - delay]
    return output_signal


# Controls the reverb time of the artificial reverb
def calculate_reverb_time(reverb_time_in_seconds, delay, sampling_freq):
    delays = np.size(delay)
    plain_gains = np.zeros(delays)
    for n in np.arange(delays):
        plain_gains[n] = 10 ** (-3 * plain_delay[n] / ((reverb_time_in_seconds / 1000) * sampling_freq))
    return plain_gains


def allpass_reverb(input_signal, filter_coefficient, delay):
    input_length = np.size(input_signal)
    output_signal = np.zeros(input_length)

    for n in np.arange(input_length):
        if n < delay:
            output_signal[n] = input_signal[n]
        else:
            output_signal[n] = filter_coefficient * input_signal[n] + input_signal[n - delay] - \
                               filter_coefficient * output_signal[n - delay]
    return output_signal


def shroeders_reverb(input_signal, mix_parameters, plain_delays, plain_filter_coefficients, allpass_delays,
                     ap_filter_coefficients):
    input_length = np.size(input_signal)
    output_signal = np.zeros(input_length)

    # run plain reverb in parallel
    n_plain_reveberators = np.size(plain_delays)
    for n in np.arange(n_plain_reveberators):
        output_signal = output_signal + \
                        mix_parameters[n] * plain_reverb(input_signal, plain_filter_coefficients[n], plain_delays[n])
    # run the allpass reverb in series
    n_allpass_reverberaters = np.size(allpass_delays)
    for n in np.arange(n_allpass_reverberaters):
        output_signal = allpass_reverb(output_signal, ap_filter_coefficients[n], allpass_delays[n])
    return output_signal


# # # recording
# sampling_freq = 44100
# sd.default.samplerate = sampling_freq
# sd.default.channels = (1, 5)
# rec_time = 5  # seconds
#
# mic_data = sd.rec(rec_time * sampling_freq)
#
# print("Recording...")
# sd.wait()
# print("Recording ended.")
# print(mic_data)

mix_parameters = np.array([0.3, 0.25, 0.25, 0.2])  # the gain of the reverb of the plain reverbs
plain_delay = np.array([3001, 3137, 2927, 2539])  # the delay of the plain reverb, has to be prime numbers
# plain_delay = np.array([1553, 1613, 1495, 1153])
allpass_delay = np.array([223, 443])  # the allpass delays, should be small
allpass_filter_coefficients = np.array(
        [-0.7, -0.7])  # the allpass filter coefficients which should be less than 0

root = Tk()
root.title("Schroeders delay")
root.geometry("260x200")
delay_variable = DoubleVar()
delay_scale = Scale(root, variable=delay_variable, from_=0, to=4000, orient=HORIZONTAL, label="delay in ms")
delay_scale.pack(anchor=CENTER)
delay_scale.pack()
mix_variable = DoubleVar()
mix_scale = Scale(root, variable=mix_variable, orient=HORIZONTAL, label="Dry/Wet mix")
mix_scale.pack(anchor=CENTER)
button = Button(root, text="Play clip", command=delay)
button.pack(anchor=CENTER)

root.mainloop()

# wave.write("short_delay_big_plain.wav", sampling_freq, wet_guitar_signal)
