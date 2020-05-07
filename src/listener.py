import csv
import numpy as np
import soundfile as sf
from src import interface, audio_io
import tkinter.filedialog as fd

interface = interface.ListenerInterface()

csv_loaded = np.array([[]])
audio_to_play = None
playback = None


def load_dependencies():
    global csv_loaded, audio_to_play

    tempdir = fd.askopenfilename(initialdir="../dependencies/csv_data",
                                 filetypes=(("Template files", "*.csv"), ("All files", "*")))
    try:
        csv_loaded = list(csv.reader(open(tempdir)))
        csv_loaded = np.array(csv_loaded)
        print(csv_loaded.shape)
    except UnicodeDecodeError:
        interface.show_error_message("Error wrong file type, expected type .csv")
        load_dependencies()
    except FileNotFoundError:
        interface.show_error_message("Error no file found")
        load_dependencies()

    tempdir = fd.askopenfilename(initialdir="../dependencies/wav_data",
                                 filetypes=(("Template files", "*.wav"), ("All files", "*")))
    try:
        audio_to_play, _ = sf.read(tempdir)
        audio_to_play = np.reshape(audio_to_play, (-1, 2)).transpose()
        print("Audio to play: ", audio_to_play.shape)
        # print(audio_to_play.shape)
    except (RuntimeError, UnicodeDecodeError):
        interface.show_error_message("Error wrong file type, expected type .wav")
        load_dependencies()
    except FileNotFoundError:
        interface.show_error_message("Error no file found")
        load_dependencies()

    return csv_loaded, audio_to_play


while interface.running:
    interface.update()

    if interface.player_controller.buttons["open_file_button"].clicked:
        # try to load in the most recently created csv and audio/wav file
        load_dependencies()

    if interface.player_controller.playback_state["started"]:

        if audio_to_play is not None:

            positional_data = np.zeros(csv_loaded.shape)
            positional_data[:, 0] = csv_loaded[:, 0].astype(int)
            positional_data[:, 1] = csv_loaded[:, 1].astype(float)
            positional_data[:, 2] = csv_loaded[:, 2].astype(int)

            playback = audio_io.DynamicPlaybackThread()
            playback.set_data(audio_to_play, positional_data)
            playback.start()

        else:
            print("No file found and you can't play nothing, idiot")
            interface.player_controller.playback_state["stopped"] = True
            interface.show_error_message("Error, no file loaded")

    elif interface.player_controller.playback_state["in_process"]:
        if audio_to_play is not None:
            if playback.done:
                interface.player_controller.playback_state["stopped"] = True
                playback.done = False
