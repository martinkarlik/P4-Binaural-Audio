import sofa
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import *
import threading

from Source import interface


class RecordingThread(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.keep_on = True
        self.mic_data = np.array([])
        self.sampling_freq = 48000
        self.rec_time = 5  # seconds
        sd.default.samplerate = self.sampling_freq
        sd.default.channels = (1, 2)

    def run(self):
        while self.keep_on:
            print("Recording new chunk.")
            current_chunk = sd.rec(self.rec_time * self.sampling_freq)
            sd.wait()
            print(self.mic_data.size)
            if self.mic_data.size == 0:
                self.mic_data = current_chunk
            else:
                self.mic_data = np.append(self.mic_data, current_chunk)

    def play(self):
        print("Playing.")
        print(self.mic_data.shape)
        sd.play(self.mic_data, self.sampling_freq)
        sd.wait()
        print("Done.")

    def get_data(self):
        return self.mic_data


interface = interface.CreatorInterface()


audio_positional_data = []
recording = RecordingThread(1)

while interface.running:
    interface.update()

    if interface.audio_manager.recording_started:
        recording.start()

    if interface.audio_manager.recording_in_process:
        pass

    elif interface.audio_manager.recording_stopped:
        recording.keep_on = False
        recording.join()

    if interface.audio_manager.playback_started:
        recording.play()


# TODO Listener Interface
# TODO Continues recording of flexible length (stopped when told to do so)