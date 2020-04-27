import threading
import sounddevice as sd
import numpy as np
import librosa
from scipy.signal import fftconvolve




class AudioIOThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_freq = 44100
        self.chunk_length = 0.03
        self.chunk_samples = int(self.sampling_freq * self.chunk_length)

        # sd.default.samplerate = self.sampling_freq
        # sd.default.channels = (1, 2)

class RecordingThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.rec_data = np.array([[]])

        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=1, blocksize=self.chunk_samples, callback=self.callback)

    def in_callback(self, indata, frames, time, status):

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
        self.done = False
        self.counter = 0

        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=1, blocksize=self.chunk_samples, callback=self.callback)

    def run(self):
        sd.play(self.play_data)
        sd.wait()
        # self.play_stream.start()
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
    #     # output = lfilter((signal[0:30000, 0]), 1, guitar_signal.transpose())
    #     #output = np.append(output.transpose(), output.transpose(), axis=1)
    #
    #     #outdata[:] = output
    #
    #     print(outdata)

    def callback(self, outdata, frames, time, status):
        outdata[:] = self.play_data[self.counter * frames:(self.counter+1) * frames]
        self.counter += 1

    def set_data(self, data):
        self.play_data = data

    # print("start")
    # input()
    # recording = RecordingThread(1)
    # recording.start()
    #
    # print("stop")
    # input()
    # recording.stop()
    # playback = PlaybackThread(2)
    # playback.set_data(recording.get_data())
    #
    # print("play")
    # input()
    # playback.start()
    #
    # input()
    # print("stopped")


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
