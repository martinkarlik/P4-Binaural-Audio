import sofa
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import *
import threading

from Source import interface
from Source import audio_processing
from Source import audio_io


interface = interface.CreatorInterface()
recording = None
playback = None

while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        recording = audio_io.RecordingThread()
        recording.start()

    if interface.audio_manager.recording_state["in_process"]:
        pass

    elif interface.audio_manager.recording_state["stopped"]:
        recording.stop()

    if interface.audio_manager.playback_state["started"]:
        playback = audio_io.PlaybackThread()
        playback.set_data(recording.get_data())
        playback.start()

    elif interface.audio_manager.playback_state["in_process"]:

        # playback.get_chunk()
        # playback.process_chunk()
        # playback.play_chunk()

        if playback.done:
            interface.audio_manager.playback_state["stopped"] = True
            playback.done = False

            audio_data = interface.audio_controller.full_audio_data
            print(audio_data)
            #
            # print(audio_data)
            # audio_data = np.array(audio_data)
            #
            # audio_processing.preprocess_data(recording.get_data(), audio_data)
