import numpy as np
from scipy.signal import *
import sofa
import librosa

forest_ir, _ = librosa.load('../dependencies/impulse_responses/forrest.wav', sr=44100)
church_ir, _ = librosa.load('../dependencies/impulse_responses/church_balcony.wav', sr=44100)
cave_ir, _ = librosa.load('../dependencies/impulse_responses/cave.wav', sr=44100)

REVERB_IR = dict(forest=forest_ir, church=church_ir, cave=cave_ir)

sofa_0_5 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_0_5m.sofa')
sofa_1 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
sofa_2 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_2m.sofa')
sofa_3 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_3m.sofa')

HR_IR = {0.225: sofa_0_5, 0.55: sofa_1, 0.775: sofa_2, 1: sofa_3}

# Both REVERB_IR and HR_IR are dictionaries, so that it's easy to access the IRs by their keys.
# For head-related IRs, it makes sense for the keys to be floats (representing distance), not strings -
# - that's why the syntax of creating the dictionary is different in both cases.


def unpack_data(rec_data, filter_data):
    # Receives filter data in form [{angle, distance, reverb_type}, duration in millis] * number of different positions,
    # splits it into binaural filter data and reverb filter data.
    # Point is, because reverb and 3d are filtered in series, we need two different filter datasets.
    # If all you change in edit mode is reverb types, i.e. you have 17 positions with different reverbs,
    # but the same angle and distance, we'd like to work with binaural filter data that has only one element:
    # the angle, the distance and the sum of the durations of these 17 "different" positions.
    # You know, otherwise it would be like: "Alright, angle 45 distance 1m for 2 sec, and then angle 45 distance 1m for
    # 3 sec, oh and now angle 45 distance 1m for 1,5 sec..." Instead of course we want angle 45 distance 1m for 6,5 sec.
    # Same thing the other way. This does that, plus some extra preprocessing work.

    # First convert duration of a position in milliseconds into percentage of recording,
    # i.e. if position lasts 2.5 seconds in a 25 second recording.. 2.5 -> 0.1
    filter_data[:, 1] = np.divide(filter_data[:, 1], np.sum(filter_data[:, 1]))

    # Convert that into the amount of samples per position (1 second == sampling freq (say 48k) of samples),
    # because samples is the unit of measurement we need to work with when processing.
    filter_data[:, 1] = np.multiply(filter_data[:, 1], len(rec_data)).astype(int)

    # Because of the rounding above, we will not divide the positions perfectly.
    # Although the error we're talking here is very tiny (handful of samples, few nanoseconds of recording),
    # we still need to designate those lost samples to some position. So let's just give them to the last one, who cares why.

    filter_data[len(filter_data) - 1][1] += abs(len(rec_data) - np.sum(filter_data[:, 1]))

    positional_data = []
    reverb_data = []
    elapsed_duration_positional = 0
    elapsed_duration_reverb = 0

    current_reverb = filter_data[0][0]["reverb"]
    current_position = (filter_data[0][0]["angle"], filter_data[0][0]["radius"])
    for i in np.arange(0, len(filter_data)):

        if filter_data[i][0]["reverb"] != current_reverb:
            reverb_data.append([current_reverb, elapsed_duration_reverb])
            elapsed_duration_reverb = 0
            current_reverb = filter_data[i][0]["reverb"]

        elapsed_duration_reverb += filter_data[i][1]

        if (filter_data[i][0]["angle"], filter_data[i][0]["radius"]) != current_position:
            positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])
            elapsed_duration_positional = 0
            current_position = (filter_data[i][0]["angle"], filter_data[i][0]["radius"])

        elapsed_duration_positional += filter_data[i][1]

    reverb_data.append([current_reverb, elapsed_duration_reverb])
    positional_data.append([current_position[0], current_position[1], elapsed_duration_positional])

    return reverb_data, positional_data


def apply_reverb_filtering(input_signal, reverbs_data):

    input_signal = np.divide(input_signal, np.max(np.abs(input_signal)))
    output_signal = np.zeros([len(input_signal), 1])

    elapsed_duration = 0

    for reverb_data in reverbs_data:
        reverb_type = reverb_data[0]
        duration = reverb_data[1]

        start_index = elapsed_duration
        elapsed_duration += duration
        end_index = elapsed_duration

        output_signal[start_index:end_index] = \
            filter_reverb(input_signal[start_index:end_index, 0], reverb_type)

    return output_signal


def filter_reverb(input_chunk, reverb_type):
    output_chunk = np.zeros([input_chunk.shape[0], 1])

    if reverb_type == "anechoic":
        output_chunk[:, 0] = input_chunk
    else:
        response = fftconvolve(input_chunk, REVERB_IR[reverb_type], mode="full")[0: len(input_chunk)]
        response = np.divide(response, np.abs(np.max(response)))

        output_chunk[:, 0] = response

    return output_chunk


def apply_binaural_filtering(input_signal, positional_data):

    input_signal = np.divide(input_signal, np.max(np.abs(input_signal)))
    output_signal = np.zeros([len(input_signal), 2])

    filter_state = None
    elapsed_duration = 0

    for position in positional_data:
        current_angle = position[0]
        current_radius = position[1]
        current_duration = position[2]

        start_index = elapsed_duration
        elapsed_duration += current_duration
        end_index = elapsed_duration

        output_signal[start_index:end_index, :], filter_state = \
            filter_binaural(input_signal[start_index:end_index, 0], current_angle, current_radius, filter_state)

    output_signal = np.divide(output_signal, np.max(np.abs(output_signal)))  # Normalize ||output||
    return output_signal


def filter_binaural(input_chunk, angle, radius, filter_state):

    output_chunk = np.zeros([input_chunk.shape[0], 2])

    if angle == -1:
        output_chunk[:, 0], output_chunk[:, 1] = input_chunk, input_chunk
        filter_state = None
    else:
        ir_ear_right = HR_IR[radius].Data.IR.get_values(indices={"M": angle, "R": 0, "E": 0})
        ir_ear_left = HR_IR[radius].Data.IR.get_values(indices={"M": angle, "R": 1, "E": 0})

        if filter_state is None:
            filter_state = np.zeros([2, 2047])

        output_chunk[:, 0], filter_state[0] = \
            lfilter(ir_ear_right, 1, input_chunk, zi=filter_state[0])

        output_chunk[:, 1], filter_state[1] = \
            lfilter(ir_ear_left, 1, input_chunk, zi=filter_state[1])

    return output_chunk, filter_state

