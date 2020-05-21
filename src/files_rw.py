import numpy as np
import pandas as pd
import soundfile as sf
import tkinter.filedialog as fd
import os.path
import csv


class FileManager:

    def __init__(self):
        self.number_of_recordings_done = 0

    @staticmethod
    def open_file_wav(sub_folder):
        tempdir = fd.askopenfilename(initialdir="../dependencies/" + sub_folder,
                                     filetypes=(("Template files", "*.wav"), ("All files", "*")))

        loaded_data, _ = sf.read(tempdir)
        return np.reshape(loaded_data, (-1, 1))

    @staticmethod
    def open_file_csv(sub_folder):
        tempdir = fd.askopenfilename(initialdir="../dependencies/" + sub_folder,
                                     filetypes=(("Template files", "*.csv"), ("All files", "*")))
        csv_loaded = np.array(list(csv.reader(open(tempdir))))
        filter_data = np.zeros(csv_loaded.shape)
        filter_data[:, 0], filter_data[:, 1], filter_data[:, 2] = \
            csv_loaded[:, 0].astype(int), csv_loaded[:, 1].astype(float), csv_loaded[:, 2].astype(int)
        return filter_data

    def save_file(self, audio_data, filter_data):
        csv_file_name = self.get_csv_file_path()
        wav_file_name = self.get_wav_file_path()
        if os.path.isfile(csv_file_name):
            while os.path.isfile(csv_file_name):
                self.number_of_recordings_done += 1
                csv_file_name = self.get_csv_file_path()
                wav_file_name = self.get_wav_file_path()
            sf.write(wav_file_name, audio_data, 44100)
            pd.DataFrame(filter_data).to_csv(csv_file_name, header=False, index=False)
        else:
            sf.write(wav_file_name, audio_data, 44100)
            pd.DataFrame(filter_data).to_csv(csv_file_name, header=False, index=False)

    def get_csv_file_path(self):
        return "../dependencies/csv_data/positional_data" + str(self.number_of_recordings_done) + ".csv"

    def get_wav_file_path(self):
        return "../dependencies/wav_data/recording_data" + str(self.number_of_recordings_done) + ".wav"


