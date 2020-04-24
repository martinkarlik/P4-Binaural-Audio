import threading
import sounddevice as sd
import numpy as np

class AudioIOThread(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.keep_on = True
        self.mic_data = np.array([])
        self.sampling_freq = 48000
        self.rec_time = 5  # seconds
        sd.default.samplerate = self.sampling_freq
        sd.default.channels = (1, 2)


class RecordingThread(AudioIOThread):

    def __init__(self, thread_id):
        super().__init__(thread_id)

    def run(self):
        while self.keep_on:
            print("Recording new chunk.")
            current_chunk = sd.rec(self.rec_time * self.sampling_freq)
            sd.wait()
            if self.mic_data.size == 0:
                self.mic_data = current_chunk
            else:
                self.mic_data = np.append(self.mic_data, current_chunk)

    def get_data(self):
        return self.mic_data


class PlaybackThread(AudioIOThread):

    def __init__(self, thread_id):
        super().__init__(thread_id)
        self.done = False

    def run(self):
        sd.play(self.mic_data)
        sd.wait()
        self.done = True


# duration = 5  # seconds
# frequency = 44100
# data = np.zeros([frequency*duration, 2])
# recording = True
#
# def callback(indata, frames, time, status):
#     if recording:
#         if status:
#             print(status)
#     data[:] = indata
#     print(data)
#
#
# striim = sd.InputStream(samplerate=frequency*duration, channels=2, blocksize=frequency*duration, callback=callback)
# striim.start()
# #sd.sleep(int(duration * 1000))
# input()
# striim.stop()
# recording=False

