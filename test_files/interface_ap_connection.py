import sofa
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import *
import threading

from src import interface

population = []





interface = interface.Interface()
while True:
    interface.update()
    current_angle = interface.get_value()
    # if recording button pressed:
    # start thread
    recording_thread = RecordingThread(1)
    recording_thread.start()



hrtf_database = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')

sampling_freq = 48000
sd.default.samplerate = sampling_freq
sd.default.channels = (1, 5)
rec_time = 5 # seconds

mic_data = sd.rec(rec_time * sampling_freq)
print("Recording...")
sd.wait()
print("Recording ended.")

# print(population)


data, sampling_freq = sf.read('../dependencies/audio_samples/sample.wav')
input_transposed_right = np.reshape(mic_data, (-1, 1)).transpose()
input_transposed_left = np.reshape(mic_data, (-1, 1)).transpose()

total_samples = mic_data.shape[0]  # this is the "a lot" number
total_different_positions = 360 # this is the "total different positions" number
# print(mic_data.shape[0])

# population = []
# for i in np.arange(total_different_positions):  # remember, np.arange() is like normal range() but on steroids
#     population.append((i, total_samples // total_different_positions if i > 0 else total_samples % total_different_positions))

output_ear_right = np.zeros([1, total_samples])
output_ear_left = np.zeros([1, total_samples])


elapsed_duration = 0  # We'll need to keep track of how much of our data we have processed already

filter_state_unknown = True
filter_state_right = 0
filter_state_left = 0

for position in population:
    angle = position[0]
    duration = position[1]

    start_index = elapsed_duration
    elapsed_duration += duration
    end_index = elapsed_duration

    if angle == -1:  # don't apply any filters, output should stay stereo
        output_ear_right[0, start_index:end_index] = input_transposed_right[0, start_index:end_index]
        output_ear_left[0, start_index:end_index] = input_transposed_left[0, start_index:end_index]
        filter_state_unknown = True
    else:
        ir_ear_right = hrtf_database.Data.IR.get_values(indices={"M": angle, "R": 0, "E": 0})
        ir_ear_left = hrtf_database.Data.IR.get_values(indices={"M": angle, "R": 1, "E": 0})

        if filter_state_unknown:
            filter_state_right = lfilter_zi(ir_ear_right, 1)
            filter_state_left = lfilter_zi(ir_ear_left, 1)
            filter_state_unknown = False

        output_ear_right[0, start_index:end_index], filter_state_right = \
            lfilter(ir_ear_right, 1, input_transposed_right[0, start_index:end_index], zi=filter_state_right)
        output_ear_left[0, start_index:end_index], filter_state_left = \
            lfilter(ir_ear_left, 1, input_transposed_left[0, start_index:end_index], zi=filter_state_left)


output = np.append(output_ear_right.transpose(), output_ear_left.transpose(), axis=1)
sd.play(output, sampling_freq)

print("Playing...")
sd.wait()
print("Playback ended.")

# sf.write("sample_modified.wav", output, sampling_freq)