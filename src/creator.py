import pandas as pd
import os.path

import sounddevice as sd
import soundfile as sf
import tkinter.filedialog as fd
import numpy as np

from src import interface
from src import audio_processing
from src import audio_io
from src import file_names

interface = interface.CreatorInterface()
recording = None
playback = None

reverb_output = None
reverb_data = []
binaural_output = None
positional_data = []

number_of_recordings_done = 0

while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        try:
            recording = audio_io.RecordingThread()
            recording.start()
        except sd.PortAudioError:
            interface.audio_manager.recording_state["stopped"] = True
            interface.show_error_message("No recognized microphone.")

    elif interface.audio_manager.recording_state["stopped"]:
        try:
            recording.stop()
        except AttributeError:
            interface.show_error_message("No recognized microphone")

    if interface.audio_manager.playback_state["started"]:
        print("Playback started")
        try:
            playback = audio_io.PlaybackThread()
            playback.set_data(binaural_output if binaural_output is not None else recording.get_data())
            playback.start()
        except AttributeError:
            interface.audio_manager.playback_state["stopped"] = True
            interface.show_error_message("Record something first.")

    elif interface.audio_manager.playback_state["in_process"]:
        try:
            if playback.done:
                interface.audio_manager.playback_state["terminated"] = True
                playback.done = False
                print("Recording done")
        except AttributeError:
            interface.show_error_message("Record something first.")

    if interface.audio_manager.edit_state["started"]:
        print("Editing started")
        try:
            playback = audio_io.PlaybackThread()
            playback.set_data(recording.get_data())
            playback.start()
        except AttributeError:
            interface.audio_manager.edit_state["stopped"] = True
            interface.show_error_message("Record something first")

    elif interface.audio_manager.edit_state["in_process"]:

        if playback.done:
            interface.audio_manager.edit_state["terminated"] = True
            playback.done = False

    if interface.audio_manager.edit_state["stopped"]:

        filter_data = interface.audio_controller.get_filter_data()

        if len(filter_data) > 0 and recording is not None:
            positional_data, reverb_data = audio_processing.unpack_data(recording.get_data(), filter_data)

            reverb_output = audio_processing.apply_reverb_filtering(recording.get_data(), reverb_data)
            binaural_output = audio_processing.apply_binaural_filtering(reverb_output, positional_data)

            interface.audio_controller.clear_filter_data()

    if interface.audio_manager.buttons["open_button"].clicked:
        tempdir = fd.askopenfilename(initialdir="../dependencies/audio_samples",
                                     filetypes=(("Template files", "*.wav"), ("All files", "*")))
        try:
            loaded_data, _ = sf.read(tempdir)
            loaded_data = np.reshape(loaded_data, (-1, 2))
            recording = audio_io.RecordingThread()
            recording.set_data(loaded_data)

            rec_time = int(loaded_data.shape[0] / recording.sampling_freq)

            minutes = f"0{rec_time // 60}" if rec_time // 60 < 10 else f"{rec_time // 60}"
            seconds = f"0{rec_time % 60}" if rec_time % 60 < 10 else f"{rec_time % 60}"

            interface.audio_manager.text_fields["recording_timer"].text = minutes + ":" + seconds

        except (RuntimeError, UnicodeDecodeError):
            interface.show_error_message("Error wrong file type, expected type .wav")
        except FileNotFoundError:
            interface.show_error_message("Error no file found")

    if interface.audio_manager.buttons["save_button"].clicked:

        sf.write("../dependencies/audio_samples/didnt_mean_to_save_this.wav", binaural_output, 44100)

        # ---------------------------------------- HANDLE CSV FILE -------------------------------------------------
        try:
            csv_file_name = file_names.get_csv_file_path()
            wav_file_name = file_names.get_wav_file_path()
            if os.path.isfile(csv_file_name):
                while os.path.isfile(csv_file_name):
                    file_names.increase_number_of_recordings_created()
                    csv_file_name = file_names.get_csv_file_path()
                    wav_file_name = file_names.get_wav_file_path()
                sf.write(wav_file_name, recording.get_data(), 44100)
                pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
            else:
                pd.DataFrame(positional_data).to_csv(csv_file_name, header=False, index=False)
                sf.write(wav_file_name, recording.get_data(), 44100)

            print("Saved!")
        except AttributeError:
            interface.show_error_message("Record, and play something first")
        except ValueError:
            print("I have no clue, but like stop trying to record a second time will ya?")
