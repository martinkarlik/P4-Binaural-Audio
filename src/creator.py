import numpy as np
import sounddevice as sd
import pandas as pd
import os.path
import csv
import soundfile as sf

from src import interface
from src import audio_processing
from src import audio_io
from src import file_names

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

        print("rec shape", recording.get_data().shape)

        output = audio_processing.apply_binaural_filtering(recording.get_data(), positional_data)

        print("output shape", output.shape)
        sd.play(output)
        sd.wait()

        # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------

        # Wasn't sure which block of code for this csv to choose when merging, deal with this information accordingly
        csv_file_name = file_names.get_csv_file_path()
        wav_file_name = file_names.get_wav_file_path()
        if os.path.isfile(csv_file_name):
            file_names.increase_number_of_recordings_created()
            sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)
            pd.DataFrame(positional_data).to_csv(csv_file_name, header=None, index=None)
        else:
            pd.DataFrame(positional_data).to_csv(csv_file_name, header=None, index=None)
            sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)
        break

        # csv_file_name = "../dependencies/csv_data/positional_data" + str(number_of_recordings_done) + ".csv"
        # if not os.path.isfile(csv_file_name):
        #     pd.DataFrame(positional_data).to_csv(csv_file_name, header=None, index=None)
        #     number_of_recordings_done += 1
        # csv_loaded = list(csv.reader(open(csv_file_name)))
        # csv_loaded = np.array(csv_loaded)
        # print("csv shape: ", csv_loaded.shape)
        #
