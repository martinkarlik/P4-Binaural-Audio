import numpy as np
from scipy.signal import *
import sounddevice as sd
import soundfile as sf
import sofa
import librosa


def preprocess_data(rec_data, audio_data):
    total_frames = np.sum(audio_data[:, 1])
    audio_data[:, 1] = np.divide(audio_data[:, 1], total_frames)

    for sample in audio_data:
        sample[1] = int(sample[1] * len(rec_data))

    audio_data[len(audio_data) - 1][1] += abs(len(rec_data) - np.sum(audio_data[:, 1]))

    positional_data = []
    reverb_data = []
    elapsed_duration_positional = 0
    elapsed_duration_reverb = 0

    current_reverb = audio_data[0][0]["reverb"]
    current_position = (audio_data[0][0]["angle"], audio_data[0][0]["radius"])
    for i in np.arange(0, len(audio_data)):

        if audio_data[i][0]["reverb"] != current_reverb:
            reverb_data.append([current_reverb, elapsed_duration_reverb])
            elapsed_duration_reverb = 0
            current_reverb = audio_data[i][0]["reverb"]

        elapsed_duration_reverb += audio_data[i][1]

        if (audio_data[i][0]["angle"], audio_data[i][0]["radius"]) != current_position:
            positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])
            elapsed_duration_positional = 0
            current_position = (audio_data[i][0]["angle"], audio_data[i][0]["radius"])

        elapsed_duration_positional += audio_data[i][1]

    reverb_data.append([current_reverb, elapsed_duration_reverb])
    positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])

    return positional_data, reverb_data



def apply_reverb_filtering(input_signal, reverb_data):


    forest_ir = librosa.load('../dependencies/impulse_responses/forrest.wav')
    church_ir = librosa.load('../dependencies/impulse_responses/church_balcony.wav')
    cave_ir = librosa.load('../dependencies/impulse_responses/cave.wav')

    input_signal_right_transposed = np.reshape(input_signal[:, 0], (-1, 1)).transpose()
    input_signal_left_transposed = np.reshape(input_signal[:, 1], (-1, 1)).transpose()

    total_samples = len(input_signal)

    output_ear_right = np.zeros([1, total_samples])
    output_ear_left = np.zeros([1, total_samples])

    elapsed_duration = 0

    for reverb in reverb_data:
        reverb_type = reverb[0]
        duration = reverb[1]

        start_index = elapsed_duration
        elapsed_duration += duration
        end_index = elapsed_duration

        if reverb_type == "anechoic":
            output_ear_right[0, start_index:end_index] = input_signal_right_transposed[0, start_index:end_index]
            output_ear_left[0, start_index:end_index] = input_signal_left_transposed[0, start_index:end_index]
        else:
            if reverb_type == "forest":
                reverb_ir = forest_ir
            elif reverb_type == "church":
                reverb_ir = church_ir
            else:
                reverb_ir = cave_ir

            output_ear_right[0, start_index:end_index] = fftconvolve(input_signal_right_transposed[0, start_index:end_index], reverb_ir, mode="same")
            output_ear_left[0, start_index:end_index] = fftconvolve(input_signal_left_transposed[0, start_index:end_index], reverb_ir, mode="same")

    output = np.append(output_ear_right.transpose(), output_ear_left.transpose(), axis=1)
    print("playing non real time reverb output")
    sd.play(output)
    sd.wait()
    return output


def apply_binaural_filtering(input_signal, positional_data):

    sofa_0_5 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_0_5m.sofa')
    sofa_1 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
    sofa_2 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_2m.sofa')
    sofa_3 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_3m.sofa')

    hrtf_database = {0.2: sofa_0_5, 0.4: sofa_1, 0.8: sofa_2, 1.2: sofa_3}

    input_signal_right_transposed = np.reshape(input_signal[:, 0], (-1, 1)).transpose()
    input_signal_left_transposed = np.reshape(input_signal[:, 1], (-1, 1)).transpose()

    total_samples = len(input_signal)

    output_ear_right = np.zeros([1, total_samples])
    output_ear_left = np.zeros([1, total_samples])


    elapsed_duration = 0

    filter_state_unknown = True
    filter_state_right = 0
    filter_state_left = 0

    for position in positional_data:
        angle = position[0]
        radius = position[1]
        duration = int(position[2])

        start_index = elapsed_duration
        elapsed_duration += duration
        end_index = elapsed_duration

        if angle == -1:  # don't apply any filters, output should stay stereo
            output_ear_right[0, start_index:end_index] = input_signal_right_transposed[0, start_index:end_index]
            output_ear_left[0, start_index:end_index] = input_signal_left_transposed[0, start_index:end_index]
            filter_state_unknown = True
        else:
            ir_ear_right = hrtf_database[radius].Data.IR.get_values(indices={"M": angle, "R": 0, "E": 0})
            ir_ear_left = hrtf_database[radius].Data.IR.get_values(indices={"M": angle, "R": 1, "E": 0})

            if filter_state_unknown:
                filter_state_right = lfilter_zi(ir_ear_right, 1)
                filter_state_left = lfilter_zi(ir_ear_left, 1)
                filter_state_unknown = False

            output_ear_right[0, start_index:end_index], filter_state_right = \
                lfilter(ir_ear_right, 1, input_signal_right_transposed[0, start_index:end_index], zi=filter_state_right)
            output_ear_left[0, start_index:end_index], filter_state_left = \
                lfilter(ir_ear_left, 1, input_signal_left_transposed[0, start_index:end_index], zi=filter_state_left)
            # Convolve the IRs with the input and put it into output

    output = np.append(output_ear_right.transpose(), output_ear_left.transpose(), axis=1)
    print("playing non real time output")
    sd.play(output)
    sd.wait()
    return output



def split_audio_data(data):

    positional_data = []
    reverb_data = []
    elapsed_duration_positional = 0
    elapsed_duration_reverb = 0

    current_reverb = data[0][0]["reverb"]
    current_position = (data[0][0]["angle"], data[0][0]["radius"])
    for i in np.arange(0, len(data)):

        if data[i][0]["reverb"] != current_reverb:
            reverb_data.append([current_reverb, elapsed_duration_reverb])
            elapsed_duration_reverb = 0
            current_reverb = data[i][0]["reverb"]

        elapsed_duration_reverb += data[i][1]

        if (data[i][0]["angle"], data[i][0]["radius"]) != current_position:
            positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])
            elapsed_duration_positional = 0
            current_position = (data[i][0]["angle"], data[i][0]["radius"])

        elapsed_duration_positional += data[i][1]

    reverb_data.append([current_reverb, elapsed_duration_reverb])
    positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])
    print("pos data; ", positional_data)
    return positional_data, reverb_data


# sampling_freq = 48000
# sd.default.samplerate = sampling_freq
# sd.default.channels = (1, 5)
# rec_time = 10 # seconds
#
# mic_data = sd.rec(rec_time * sampling_freq)
# mic_data_transposed = mic_data.transpose()
# print("Recording...")
# sd.wait()
# print("Recording ended.")
#
# # input_transposed = np.reshape(mic_data, (-1, 1)).transpose()
#
# print(mic_data.shape)
# positional_data = [[(270, 1.2), 48000*2], [(90, 1.2), 48000*2], [(-1, 0), 48000*2], [(90, 1.2), 48000*2], [(180, 1.2), 48000*2]]
#
# output = apply_binaural_filtering(mic_data, positional_data)
# sd.play(output, sampling_freq)
# sd.wait()