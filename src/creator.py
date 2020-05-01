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

    if interface.audio_manager.buttons["save_button"].clicked:  # should be RENDER button
        audio_data = interface.audio_controller.full_audio_data

        positional_data = []
        reverb_data = []
        if len(audio_data) > 0:
            positional_data, reverb_data = audio_processing.preprocess_data(recording.get_data(), np.array(audio_data))

        # reverb_output = audio_processing.apply_reverb_filtering(recording.get_data(), reverb_data)
        binaural_output = audio_processing.apply_binaural_filtering(recording.get_data(), positional_data)

        # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------

        csv_file_name = file_names.get_csv_file_path()
        wav_file_name = file_names.get_wav_file_path()
        if os.path.isfile(csv_file_name):
            file_names.increase_number_of_recordings_created()
            sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)
            pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
        else:
            pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
            sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)



# TODO playback in creator and playback in listener
# TODO real time playback with saved positions in listener
# TODO naming the recording
