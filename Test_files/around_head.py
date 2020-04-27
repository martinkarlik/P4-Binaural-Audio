import sofa
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
from scipy.signal import *

hrtf_database = sofa.Database.open('../Dependencies/Sofa/QU_KEMAR_anechoic_1m.sofa')

# recording
sampling_freq = 48000
sd.default.samplerate = sampling_freq
sd.default.channels = (1, 5)
rec_time = 10 # seconds

mic_data = sd.rec(rec_time * sampling_freq)
mic_data_transposed = mic_data.transpose()
print("Recording...")
sd.wait()
print("Recording ended.")

# time_vector = np.arange(rec_time * sampling_freq) / sampling_freq
# sinusoid = np.reshape(0.05*np.sin(2*np.pi*600*time_vector), (-1, 1))
# sinusoid_transposed = sinusoid.transpose()

# sound convolution

output_ear1 = np.zeros([1, rec_time * sampling_freq])
output_ear2 = np.zeros([1, rec_time * sampling_freq])
filter_state1 = 0
filter_state2 = 0

number_of_positions = 360
total_samples = sampling_freq * rec_time

first_sample = True
for i in np.arange(number_of_positions):
    ir_ear1 = hrtf_database.Data.IR.get_values(indices={"M": i, "R": 0, "E": 0})
    ir_ear2 = hrtf_database.Data.IR.get_values(indices={"M": i, "R": 1, "E": 0})

    start_index = int(i * total_samples / number_of_positions)
    end_index = int((i + 1) * total_samples / number_of_positions)

    if first_sample:
        filter_state1 = lfilter_zi(ir_ear1, 1)
        filter_state2 = lfilter_zi(ir_ear2, 1)
        first_sample = False

    output_ear1[0, start_index:end_index], filter_state1 = \
        lfilter(ir_ear1, 1, mic_data_transposed[0, start_index:end_index], zi=filter_state1)
    output_ear2[0, start_index:end_index], filter_state2 = \
        lfilter(ir_ear2, 1, mic_data_transposed[0, start_index:end_index], zi=filter_state2)


# playback

output = np.append(output_ear1.transpose(), output_ear2.transpose(), axis=1)
print(output.shape)
sd.play(output)


print("Playing...")
sd.wait()
print("Playback ended.")

# plotting

time_vector = np.arange(output.shape[0])
plt.figure(figsize=(15, 5))
plt.title("Output")
legend = ["Ear1", "Ear 2"]
for i in range(2):
    plt.plot(time_vector, output[:, i])
plt.legend(legend)
plt.show()

