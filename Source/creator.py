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
recording = audio_io.RecordingThread(1)
playback = audio_io.PlaybackThread(2)

while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        recording.start()

    if interface.audio_manager.recording_state["in_process"]:
        pass

    elif interface.audio_manager.recording_state["stopped"]:
        recording.keep_on = False
        recording.join()

    if interface.audio_manager.playback_state["started"]:
        playback.mic_data = recording.get_data()
        playback.start()

    if playback.done:
        interface.audio_manager.playback_state["stopped"] = True
        playback.done = False
        print(interface.audio_controller.full_audio_data)


    # audio_data = interface.audio_controller.full_audio_data
    #
    # audio_data = np.array(audio_data)
    #
    # total_frames = np.sum(audio_data[:, 1])
    # audio_data[:, 1] = np.divide(audio_data[:, 1], total_frames)
    #
    # for sample in audio_data:
    #     sample[1] = int(sample[1] * len(rec_data))
    #
    # audio_data[len(audio_data) - 1][1] += abs(len(rec_data) - np.sum(audio_data[:, 1]))
    #
    # positional_data, reverb_data = audio_processing.split_audio_data(audio_data)
    #
    # output = audio_processing.apply_binaural_filtering(rec_data, positional_data)
    # sd.play(output)
    # sd.wait()



        # tmp_reverb_signal = audio_processing.add_reverb(rec_data, recording.sampling_freq, interface.audio_controller.current_audio_data)
    # if interface.audio_manager.playback_started:
    #     recording.play()


# TODO Listener Interface
# TODO Continues recording of flexible length (stopped when told to do so)