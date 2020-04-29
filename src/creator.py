import numpy as np
import sounddevice as sd
import pandas as pd
import csv
import os.path

from src import interface
from src import audio_processing
from src import audio_io

interface = interface.CreatorInterface()
recording = None
playback = None

number_of_recordings_done = 0

while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        recording = audio_io.RecordingThread()
        recording.start()

    elif interface.audio_manager.recording_state["stopped"]:
        recording.stop()

    if interface.audio_manager.playback_state["started"]:
        playback = audio_io.PlaybackThread()
        playback.set_data(recording.get_data())
        playback.start()

    elif interface.audio_manager.playback_state["in_process"]:

        if playback.done:
            interface.audio_manager.playback_state["stopped"] = True
            playback.done = False

    elif interface.audio_manager.playback_state["stopped"]:

        audio_data = interface.audio_controller.full_audio_data

        positional_data = []
        reverb_data = []
        if len(audio_data) > 0:
            positional_data, reverb_data = audio_processing.preprocess_data(recording.get_data(), np.array(audio_data))

        print(positional_data)
        print(reverb_data)
        break

        # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------

        csv_file_name = "../dependencies/csv_data/positional_data" + str(number_of_recordings_done) + ".csv"
        if not os.path.isfile(csv_file_name):
            pd.DataFrame(positional_data).to_csv(csv_file_name, header=None, index=None)
            number_of_recordings_done += 1
        csv_loaded = list(csv.reader(open(csv_file_name)))
        csv_loaded = np.array(csv_loaded)
        print("csv shape: ", csv_loaded.shape)

        output = audio_processing.apply_binaural_filtering(recording.get_data(), positional_data)
        sd.play(output)
        sd.wait()

