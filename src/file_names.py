number_of_recordings_done = 0
csv_file_name = ""


def get_csv_file_path():
    global number_of_recordings_done
    return "../dependencies/csv_data/positional_data" + str(number_of_recordings_done) + ".csv"


def increase_number_of_recordings_created():
    global number_of_recordings_done
    number_of_recordings_done += 1



def get_wav_file_path():
    global number_of_recordings_done
    return "../dependencies/wav_data/recording_data" + str(number_of_recordings_done) + ".wav"
