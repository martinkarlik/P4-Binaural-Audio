from src import interface, audio_io, files_rw

interface = interface.ListenerInterface()
file_manager = files_rw.FileManager()

binaural_data = dict(audio_data=None, filter_data=None)
playback_thread = None


def load_dependencies():

    try:
        audio_data = file_manager.open_file_wav("wav_data")

    except (RuntimeError, UnicodeDecodeError):
        interface.show_error_message("Error wrong file type, expected type .wav")
        return None, None
    except FileNotFoundError:
        interface.show_error_message("Error no file found")
        return None, None

    try:
        filter_data = file_manager.open_file_csv("csv_data")
    except UnicodeDecodeError:
        interface.show_error_message("Error wrong file type, expected type .csv")
        return None, None
    except FileNotFoundError:
        interface.show_error_message("Error no file found")
        return None, None

    return audio_data, filter_data


while interface.running:
    interface.update()

    if interface.player_controller.buttons["open_file_button"].clicked:
        # try to load in the most recently created csv and audio/wav file
        binaural_data["audio_data"], binaural_data["filter_data"] = load_dependencies()

    if interface.player_controller.playback_state["started"]:

        if binaural_data["audio_data"] is not None:

            playback_thread = audio_io.DynamicPlaybackThread()
            playback_thread.set_data(binaural_data["audio_data"], binaural_data["filter_data"])
            playback_thread.start()

        else:
            print("No file found and you can't play nothing, idiot")
            interface.player_controller.playback_state["stopped"] = True
            interface.show_error_message("Error, no file loaded.")

    elif interface.player_controller.playback_state["in_process"]:
        if binaural_data["audio_data"] is not None:
            if playback_thread.done:
                interface.player_controller.playback_state["stopped"] = True
                playback_thread.done = False

