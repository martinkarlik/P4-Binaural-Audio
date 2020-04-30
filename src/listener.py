import csv
import numpy as np
import soundfile as sf
from src import interface, audio_io
from src import file_names
import tkinter
import tkinter.filedialog as fd
import os

interface = interface.ListenerInterface()

audio_to_play = None
playback = None

while interface.running:
    interface.update()

    if interface.player_controller.buttons["open_file_button"].clicked:
        try:
            # csv_loaded = list(csv.reader(open(file_names.get_csv_file_path())))
            # csv_loaded = np.array(csv_loaded)
            root = tkinter.Tk()
            root.withdraw()  # use to hide tkinter window
            currdir = os.getcwd()
            tempdir = fd.askopenfilename(filetypes = (("Template files", "*.wav"), ("All files", "*")))
            audio_to_play, _ = sf.read(tempdir)
            audio_to_play = np.reshape(audio_to_play, (-1, 2))
            print(audio_to_play.shape)
            # print(audio_to_play)
            # for i in csv_loaded:
            #     print(i)
        except:
            print("No you fool, you gotta create something first. LET'S GET CREATIVE")
            print(FileNotFoundError)

    if interface.player_controller.playback_state["started"]:
        playback = audio_io.PlaybackThread()
        # TODO get mic data and positional data to work with playback
        playback.set_data(audio_to_play)
        playback.start()

    elif interface.player_controller.playback_state["in_process"]:

        if playback.done:
            interface.player_controller.playback_state["stopped"] = True
            playback.done = False

