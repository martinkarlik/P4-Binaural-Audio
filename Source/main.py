import sofa
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import *
import threading

from Source import UI_class


class RecordingThread(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.data = None

    def run(self):
        self.data = sd.rec()

    def get_data(self):
        return self.data


interface = UI_class.CreationInterface()


running = True
is_recording = False

population = []
recording = RecordingThread(1)

while running:
    interface.get_events()

    if is_recording:
        if interface.new_position_registered:
            population.append((interface.get_new_position(), interface.get_time_stamp()))
    else:
        if interface.recording_button_pressed:
            recording.start()

    interface.update()