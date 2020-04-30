import threading

import sofa
import sounddevice as sd
import numpy as np
import librosa
from scipy.signal import fftconvolve
from scipy.signal import *

signal, sampling_freq = librosa.load('../dependencies/impulse_responses/church_balcony.wav', sr=44100)
signal = np.reshape(signal, (-1, 1))
hrtf_database = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
ir_ear1 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 0, "E": 0})
ir_ear2 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 1, "E": 0})


class AudioIOThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_freq = 44100
        self.chunk_length = 0.05
        self.chunk_samples = int(self.sampling_freq * self.chunk_length)

        # sd.default.samplerate = self.sampling_freq
        # sd.default.channels = (1, 2)


class RecordingThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.rec_data = np.array([[]])

        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                         callback=self.callback)

    def callback(self, indata, frames, time, status):

        if self.rec_data.size == 0:
            self.rec_data = indata
        else:
            self.rec_data = np.append(self.rec_data, indata, axis=0)

    def run(self):
        self.rec_stream.start()

    def stop(self):
        self.rec_stream.stop()
        self.rec_data = np.array(self.rec_data)

    def get_data(self):
        return self.rec_data


class PlaybackThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.play_data = np.array([[]])

        self.output_ear1 = np.array([[]])
        self.output_ear2 = np.array([[]])

        self.positional_data = [[10, 20, 7000], [10, 20, 8000], [10, 20, 10000], [10, 20, 5000]]

        self.filter_state1 = 0
        self.filter_state2 = 0
        self.done = False

        self.chunk_index = 0

        sofa_0_5 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_0_5m.sofa')
        sofa_1 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
        sofa_2 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_2m.sofa')
        sofa_3 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_3m.sofa')

        self.hrtf_database = {0.2: sofa_0_5, 0.4: sofa_1, 0.8: sofa_2, 1.2: sofa_3}
        self.filter_state_left = None
        self.filter_state_right = None

        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                           callback=self.callback)

    def run(self):
        self.play_stream.start()

    def callback(self, outdata, frames, time, status):

        play_data_transposed = self.play_data.transpose()

        pos_data = [2200, 7000, 4700]

        0-1200, 1200-2400, 2400-3600

        self.chunk_index * frames

        # Find position that corresponds to the middle of the chunk!

        start_index = self.chunk_index * frames
        end_index = (self.chunk_index + 1) * frames

        ir_ear_right = self.hrtf_database[0.8].Data.IR.get_values(
            indices={"M": self.chunk_index, "R": 0, "E": 0})
        ir_ear_left = self.hrtf_database[0.8].Data.IR.get_values(
            indices={"M": (self.chunk_index * 4) % 360, "R": 1, "E": 0})

        if self.filter_state_left is None and self.filter_state_right is None:
            self.filter_state_left = np.zeros([len(ir_ear_left) - 1])
            self.filter_state_right = np.zeros([len(ir_ear_left) - 1])

        outdata[:, 0], self.filter_state_left = \
            lfilter(ir_ear_left, 1, play_data_transposed[0, start_index:end_index], zi=self.filter_state_left)
        outdata[:, 1], self.filter_state_right = \
            lfilter(ir_ear_right, 1, play_data_transposed[1, start_index:end_index], zi=self.filter_state_right)

        outdata[:, 0] = play_data_transposed[0, start_index:end_index]
        outdata[:, 1] = play_data_transposed[1, start_index:end_index]

        self.chunk_index += 1

        if self.chunk_index + 1 == len(self.play_data) / frames:
            self.done = True
            self.play_stream.stop()
            print("stopped")

    def set_data(self, data):
        self.play_data = data

#
# print("start")
# recording = RecordingThread()
# recording.start()
#
# input()
# print("stop")
# recording.stop()
# playback = PlaybackThread()
# playback.set_data(recording.get_data())
#
# print("play")
# input()
# playback.start()
#
# input()
