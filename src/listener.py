import csv
import numpy as np
import soundfile as sf
from src import interface, audio_io
from src import file_names
from tkinter import messagebox
import tkinter
import tkinter.filedialog as fd
import os

interface = interface.ListenerInterface()

csv_loaded = np.array([[]])
audio_to_play = None
playback = None

while interface.running:
    interface.update()

    if interface.player_controller.buttons["open_file_button"].clicked:
        # try to load in the most recently created csv and audio/wav file
        try:
            csv_loaded = list(csv.reader(open(file_names.get_csv_file_path())))
            csv_loaded = np.array(csv_loaded)
            print(csv_loaded[0, 0])
            # for i in csv_loaded:
            #     print(i)

            # Tkinter is for if we want the user to choose a wav file instead of just playing the most recent
            # root = tkinter.Tk()
            # root.withdraw()  # use to hide tkinter window
            # currdir = os.getcwd()
            # tempdir = fd.askopenfilename(filetypes = (("Template files", "*.wav"), ("All files", "*")))
            # audio_to_play, _ = sf.read(tempdir)

            audio_to_play, _ = sf.read(file_names.get_wav_file_path())
            audio_to_play = np.reshape(audio_to_play, (-1, 2))
            print(audio_to_play.shape)
        except FileNotFoundError:
            print("No you fool, you gotta create something first. LET'S GET CREATIVE")
            # hide main window
            root = tkinter.Tk()
            root.withdraw()
            # show an error box for the user
            messagebox.showinfo("ERROR", "Error, no files found")

    if interface.player_controller.playback_state["started"]:
        playback = audio_io.PlaybackThread()
        # TODO get mic data and positional data to work with playback
        playback.set_data(audio_to_play, csv_loaded, creator=False)
        playback.start()

    elif interface.player_controller.playback_state["in_process"]:

        if playback.done:
            interface.player_controller.playback_state["stopped"] = True
            playback.done = False
