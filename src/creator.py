import tkinter
from tkinter import messagebox
import numpy as np
import pandas as pd
import os.path

import sounddevice
import soundfile as sf

from src import interface
from src import audio_processing
from src import audio_io
from src import file_names
from src.interface import show_error_message

root = interface.root
interface = interface.CreatorInterface()
recording = None
playback = None
number_of_recordings_done = 0


while interface.running:
    interface.update()
    root.withdraw()

    if interface.audio_manager.recording_state["started"]:
        try:
            recording = audio_io.RecordingThread()
            recording.start()
        except sounddevice.PortAudioError:
            interface.audio_manager.recording_state["stopped"] = True
            show_error_message("JAKUB STOP")

    # elif interface.audio_manager.recording_state["in_process"]

    elif interface.audio_manager.recording_state["stopped"]:
        recording.stop()

    if interface.audio_manager.playback_state["started"]:
        print("Recording started")
        try:
            playback = audio_io.PlaybackThread()
            playback.set_data(recording.get_data())
            playback.start()
        except AttributeError:
            interface.audio_manager.playback_state["stopped"] = True
            show_error_message("Record something first")

    elif interface.audio_manager.playback_state["in_process"]:
        print("Recording in process")
        try:
            if playback.done:
                interface.audio_manager.playback_state["stopped"] = True
                playback.done = False
                print("Recording done")
        except AttributeError:
            interface.audio_manager.playback_state["stopped"] = True
            show_error_message("Record something first")

    if interface.audio_manager.buttons["save_button"].clicked:  # should be RENDER button
        print("Rendering")
        try:
            audio_data = interface.audio_controller.full_audio_data

            positional_data = []
            reverb_data = []
            if len(audio_data) > 0:
                positional_data, reverb_data = audio_processing.preprocess_data(recording.get_data(), np.array(audio_data))

            # reverb_output = audio_processing.apply_reverb_filtering(recording.get_data(), reverb_data)
            # sf.write("../dependencies/audio_samples/stereo_sample_dk.wav", recording.get_data(), 41100)
            binaural_output = audio_processing.apply_binaural_filtering(recording.get_data(), positional_data)

            # sf.write("../dependencies/audio_samples/binaural_sample_dk.wav", binaural_output, 41100)
            break


            # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------

            csv_file_name = file_names.get_csv_file_path()
            wav_file_name = file_names.get_wav_file_path()
            if os.path.isfile(csv_file_name):
                while os.path.isfile(csv_file_name):
                    file_names.increase_number_of_recordings_created()
                    csv_file_name = file_names.get_csv_file_path()
                    wav_file_name = file_names.get_wav_file_path()
                sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)
                pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
            else:
                pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
                sf.write(wav_file_name, recording.get_data(), audio_io.sampling_freq)
        except AttributeError:
            show_error_message("Record, and play something first")

# TODO naming the recording
