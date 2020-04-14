import sofa
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import *

# Different distances (0.5m, 1m, 2m, 3m) are in 4 different sofa files, we load just one for now.
hrtf_database = sofa.Database.open('../Dependencies/Sofa/QU_KEMAR_anechoic_1m.sofa')

data, sampling_freq = sf.read('../Dependencies/Audio/sample.wav')
# Don't mind the recording.. I had no idea what to record xD

input_transposed_right = np.reshape(data[:, 0], (-1, 1)).transpose()
input_transposed_left = np.reshape(data[:, 1], (-1, 1)).transpose()
# We need inputs from left and right ear separately, to apply IRs for left ear on the left ear input and vice versa,
# so we need to split the data (of shape (a lot, 2)) into right and left ear.
# data[:, 0/1] is right / left ear of shape (a lot,). It has only one dimension, cause it is an array.
# We need to make it a vector of shape (a lot, 1). Basically doing nothing to the data itself, just
# making it 2 dimensional, even though it has just one row. This is done by np.reshape(data[:, 0/1], (-1, 1))
# Than we need to transpose it (make it (1, a lot) instead of (a lot, 1)).. because of.. reasons..
# .. because if we don't transpose it we will have red sentences in our console and who likes red sentences huh not me

total_samples = data.shape[0]  # this is the "a lot" number
total_different_positions = 360 # this is the "total different positions" number
# if the recording is "narrator for 10 sec, guy talking at 90 deg for 10 sec, narrator for 20 sec",
# total_samples is sampling_freq * 40 sec and total_different_positions is 3

# Now that we wrote 6 lines of code and one novel of comments,
# we're gonna create a data structure that will store all the transforming information.
# I think the most efficient way to store it is like so
# data = [(angle (0 - 360 and -1 for stereo), duration (in samples), optionally other effects (say 0-5 for different reverbs), ...]
# so, an example: data = [(-1, 48000, 0), (300, 2000, 1), (305, 2000, 1), (310, 2000, 1), (-1, 48000, 0)]
# Let's now, for the sake of me being bored and you being tired but weirdly excited about what this
# fucker has to write, consider alternatives and why they suck.
# Alternative number 1: Sample the recording evenly with a certain sampling rate and forget how long each position lasts.
# example: sampling_rate = 200, data = [-1, -1, -1, ..., -1, 300, 300, 300, ..., 300, -1, -1, -1, ..., -1]
# so when processing, every 200 samples we would apply new filter.. extremely inefficient if the positions don't change frequently.
# Alternative number 2: There is no other alternative, I tricked you.
# Alternative number 3: Why would there be alternative number 3 if there is no alternative number 2 are you stchupid


# The transforming data should be populated from the user interface, but let's just make it go around the head for.. a reason
# "population" might not be the best name for it, but it sounds professional, which makes me feel like I know what Im doing
population = []
for i in np.arange(total_different_positions):  # remember, np.arange() is like normal range() but on steroids
    population.append((i, total_samples // total_different_positions if i > 0 else total_samples % total_different_positions))
    # Quite an important thing to notice is that durations of all positions need to sum up to the total samples. Soo
    # split the total_samples (e.g. 720 000) evenly between total_different_positions (e.g. 360), but because it might not be
    # an integer, take the mod of it once. (say you have 13 samples and 5 positions - it would be split like [1, 3, 3, 3, 3]..
    # this is just an example of making it go around the head


# The size of the output is the same as the size of the input, which is derived from the commonly known law of energy preservation,
# which states: One cannot create nor destroy energy between the input and output link, if one is stchupid.
output_ear_right = np.zeros([1, total_samples])
output_ear_left = np.zeros([1, total_samples])

# We'll need to keep track of how much of our data we have processed already
elapsed_duration = 0

# And we'll need to recalculate the filter state everytime we lose track of it (a.k.a. turn to stereo and back)
filter_state_unknown = True
filter_state_right = 0
filter_state_left = 0

for position in population:
    # We'll now go through each position in the data, and compute the output.
    # Each column in population is (angle, duration, possibly reverb type)
    angle = position[0]
    duration = position[1]

    # We need to know where in the output to put the filtered audio, but worry not, we are storing the duration for a reason
    start_index = elapsed_duration
    elapsed_duration += duration
    end_index = elapsed_duration
    # I kinda like this, it's like.. start_index is set to elapsed_duration, and end_index is also set to elapsed_duration, but how??
    # The elapsed_duration changes between them, ahaaa!

    if angle == -1:  # don't apply any filters, output should stay stereo
        output_ear_right[0, start_index:end_index] = input_transposed_right[0, start_index:end_index]
        output_ear_left[0, start_index:end_index] = input_transposed_left[0, start_index:end_index]
        filter_state_unknown = True
        # We can index into a matrix like above with colons.
        # Example: random_matrix[0:10, 0] = 1 would set only the selected indices to 1.
        # So here, basically copy the input chunk and put it into output chunk.
    else:
        # If the sound is coming from an angle (value is not -1), we have an obligation for some sweet filtering
        ir_ear_right = hrtf_database.Data.IR.get_values(indices={"M": angle, "R": 0, "E": 0})
        ir_ear_left = hrtf_database.Data.IR.get_values(indices={"M": angle, "R": 1, "E": 0})
        # Get the IRs for the current angle

        if filter_state_unknown:
            # If last time you were stereo or you're the first position, we need to calculate the filter_state
            # .. otherwise we will remember it from previous filtering
            filter_state_right = lfilter_zi(ir_ear_right, 1)
            filter_state_left = lfilter_zi(ir_ear_left, 1)
            filter_state_unknown = False

        output_ear_right[0, start_index:end_index], filter_state_right = \
            lfilter(ir_ear_right, 1, input_transposed_right[0, start_index:end_index], zi=filter_state_right)
        output_ear_left[0, start_index:end_index], filter_state_left = \
            lfilter(ir_ear_left, 1, input_transposed_left[0, start_index:end_index], zi=filter_state_left)
        # Convolve the IRs with the input and put it into output


output = np.append(output_ear_right.transpose(), output_ear_left.transpose(), axis=1)
sd.play(output, sampling_freq)

print("Playing...")
sd.wait()
print("Playback ended.")


# sf.write("sample_modified.wav", output, sampling_freq)