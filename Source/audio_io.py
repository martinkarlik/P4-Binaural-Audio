import threading
import sounddevice as sd
import numpy as np
import librosa
from scipy.signal import fftconvolve




class AudioIOThread(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.sampling_freq = 44100


class RecordingThread(AudioIOThread):

    def __init__(self, thread_id):
        super().__init__(thread_id)

        self.chunk_length = 0.03
        self.total_samples = int(self.sampling_freq * self.chunk_length)

        # sd.default.samplerate = self.sampling_freq
        # sd.default.channels = (1, 2)

        self.mic_data = np.array([[]])
        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.total_samples, callback=self.in_callback)

    def in_callback(self, indata, frames, time, status):

        if self.mic_data.size == 0:
            self.mic_data = indata
        else:
            self.mic_data = np.append(self.mic_data, indata, axis=0)

        print(self.mic_data.shape)

    def run(self):
        self.rec_stream.start()

    def stop(self):
        self.rec_stream.stop()
        self.mic_data = np.array(self.mic_data)
        print(self.mic_data.shape)

    def get_data(self):
        return self.mic_data


class PlaybackThread(AudioIOThread):

    def __init__(self, thread_id):
        super().__init__(thread_id)
        self.done = False

        self.chunk_length = 0.05
        self.total_samples = int(self.sampling_freq * self.chunk_length)

        self.mic_data = np.array([[]])
        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.total_samples, callback=self.out_callback)

    def out_callback(self, outdata, frames, time, status):

        signal, sampling_freq = librosa.load('../Dependencies/Audio/church_balcony.wav', sr=44100)
        signal = np.reshape(signal, (-1, 1))

        print(self.mic_data)
        outdata[:] = self.mic_data

        #output = fftconvolve(indata, signal, mode="full")
        # output = lfilter((signal[0:30000, 0]), 1, guitar_signal.transpose())
        #output = np.append(output.transpose(), output.transpose(), axis=1)



    def run(self):
        self.play_stream.start()
        sd.wait()
        self.done = True

    def set_data(self, data):
        self.mic_data = data

print("start")
input()
recording = RecordingThread(1)
recording.start()

print("stop")
input()
recording.stop()
playback = PlaybackThread(2)
playback.set_data(recording.get_data())

print("play")
input()
playback.start()

input()
print("stopped")

