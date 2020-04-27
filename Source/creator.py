import sofa
import numpy as np
import sounddevice as sd
import pandas as pd
import csv
import os.path
import soundfile as sf
from scipy.signal import *
import threading

from Source import interface
from Source import audio_processing
from Source import audio_io

interface = interface.CreatorInterface()
recording = None
playback = None

number_of_recordings_done = 0

while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        recording = audio_io.RecordingThread(1)
        recording.start()

    if interface.audio_manager.recording_state["in_process"]:
        pass

    elif interface.audio_manager.recording_state["stopped"]:
        recording.stop()

    if interface.audio_manager.playback_state["started"]:
        playback = audio_io.PlaybackThread(2)
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
            # print(audio_data)
            audio_data = np.array(audio_data)
            # print(audio_data)
            # print(audio_data.shape)

            total_frames = np.sum(audio_data[:, 1])
            audio_data[:, 1] = np.divide(audio_data[:, 1], total_frames)

            for sample in audio_data:
                sample[1] = int(sample[1] * len(recording.get_data()))

            audio_data[len(audio_data) - 1][1] += abs(len(recording.get_data()) - np.sum(audio_data[:, 1]))

            positional_data, reverb_data = audio_processing.split_audio_data(audio_data)

            # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------

            csv_file_name = "../Dependencies/csv_data/positional_data" + str(number_of_recordings_done) + ".csv"
            if not os.path.isfile(csv_file_name):
                pd.DataFrame(positional_data).to_csv(csv_file_name, header=None, index=None)
                number_of_recordings_done += 1
            csv_loaded = list(csv.reader(open(csv_file_name)))
            csv_loaded = np.array(csv_loaded)
            print("csv shape: ", csv_loaded.shape)

            output = audio_processing.apply_binaural_filtering(recording.get_data(), positional_data)
            sd.play(output)
            sd.wait()

        # sd.play(output)
        # sd.wait()

        # tmp_reverb_signal = audio_processing.add_reverb(rec_data, recording.sampling_freq, interface.audio_controller.current_audio_data)
    # if interface.audio_manager.playback_started:
    #     recording.play()

# TODO Listener Interface
# TODO Continues recording of flexible length (stopped when told to do so)
