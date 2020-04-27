import threading
import sounddevice as sd
import numpy as np


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
        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.total_samples, callback=self.callback)

    def callback(self, indata, frames, time, status):

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
        self.mic_data = None

    def run(self):
        sd.play(self.mic_data, self.sampling_freq)
        sd.wait()
        self.done = True

    def set_data(self, data):
        self.mic_data = data
