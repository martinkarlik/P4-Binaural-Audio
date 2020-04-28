import threading

import sofa
import sounddevice as sd
import numpy as np
import librosa
from scipy.signal import fftconvolve, lfilter_zi, lfilter

from Source import creator

signal, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=44100)
signal = np.reshape(signal, (-1, 1))
hrtf_database = sofa.Database.open('../Dependencies/Sofa/QU_KEMAR_anechoic_1m.sofa')
ir_ear1 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 0, "E": 0})
ir_ear2 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 1, "E": 0})


class AudioIOThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_freq = 44100
        self.chunk_length = 0.5
        self.chunk_samples = int(self.sampling_freq * self.chunk_length)

        # sd.default.samplerate = self.sampling_freq
        # sd.default.channels = (1, 2)


class RecordingThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.rec_data = np.array([[]])

        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=1, blocksize=self.chunk_samples,
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
        self.filter_state1 = 0
        self.filter_state2 = 0
        self.done = False
        self.counter = 0

        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                           callback=self.callback)

    def run(self):
        # sd.play(self.play_data)
        # sd.wait()
        self.play_stream.start()
        self.done = True

    # def out_callback(self, indata, outdata, frames, time, status):
    #
    #     signal, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=44100)
    #     signal = np.reshape(signal, (-1, 1))
    #
    #     #current_chunk = 0
    #
    #     for x in range(int(len(self.mic_data)/self.total_samples)):
    #         current_chunk = x * self.total_samples
    #         if len(indata) == 0:
    #             indata[:] = self.mic_data[0:self.total_samples]
    #         else:
    #             indata[:] = self.mic_data[0 + current_chunk:self.total_samples + current_chunk]
    #         print(current_chunk)
    #
    #
    #
    #
    #     #output = fftconvolve(indata, signal, mode="full")
    #     #output = np.append(output.transpose(), output.transpose(), axis=1)
    #
    #     #outdata[:] = output
    #
    #     print(outdata)

    def callback(self, outdata, frames, time, status):
        # checks to see if there are still chunks left to process
        if self.counter * frames < len(self.play_data) - 1:

            ir_ear1 = hrtf_database.Data.IR.get_values(indices={"M": 90, "R": 0, "E": 0})
            ir_ear2 = hrtf_database.Data.IR.get_values(indices={"M": 90, "R": 1, "E": 0})

            self.output_ear1 = lfilter(ir_ear1, 1, self.play_data[self.counter * frames:(self.counter + 1) * frames, :].transpose())
            self.output_ear2 = lfilter(ir_ear2, 1, self.play_data[self.counter * frames:(self.counter + 1) * frames, :].transpose())
            # playback
            outdata[:] = np.append(self.output_ear1.transpose(), self.output_ear2.transpose(), axis=1) * 5

            # outdata[:] = self.play_data[self.counter * frames:(self.counter + 1) * frames]
            # print(outdata)
            self.counter += 1
        else:
            self.play_stream.stop()

    def set_data(self, data):
        self.play_data = data


input()
print("started")
recording = RecordingThread()
recording.start()

input()
print("stopped")
recording.stop()
playback = PlaybackThread()
playback.set_data(recording.get_data())

input()
print("playing")
playback.start()

input()
print("stopped")

# sampling_freq = 48000
# sd.default.samplerate = sampling_freq
# sd.default.channels = (1, 5)
# rec_time = 3 # seconds
#
# mic_data = sd.rec(rec_time * sampling_freq)
# mic_data_transposed = mic_data.transpose()
# print("Recording...")
# sd.wait()
# print("Recording ended.")
#
# chunk_length = 0.05
#
# chunk_samples = int(sampling_freq * chunk_length)
#
#
# def callback(outdata, frames, time, status):
#     print("frames ", frames)
#     print("time ", time.currentTime)
#     outdata[:] = mic_data[0:frames]
#
#
# play_stream = sd.OutputStream(samplerate=sampling_freq, channels=1, blocksize=chunk_samples, callback=callback)
# play_stream.start()
#
# sd.wait()
# play_stream.stop()
