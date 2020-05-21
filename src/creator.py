from src import interface, audio_io, audio_processing, files_rw
from sounddevice import PortAudioError

interface = interface.CreatorInterface()
file_manager = files_rw.FileManager()

recording_thread = None
playback_thread = None

binaural_data = dict(audio_data=None, filter_data=None)
reverb_data = dict(audio_data=None, filter_data=None)


while interface.running:
    interface.update()

    if interface.audio_manager.recording_state["started"]:
        try:
            recording_thread = audio_io.RecordingThread()
            recording_thread.start()
        except PortAudioError:
            interface.audio_manager.recording_state["stopped"] = True
            interface.show_error_message("No recognized microphone.")

    elif interface.audio_manager.recording_state["stopped"]:
        try:
            recording_thread.stop()
        except AttributeError:
            interface.show_error_message("No recognized microphone.")

    if interface.audio_manager.playback_state["started"]:
        print("Playback started")
        try:
            playback_thread = audio_io.PlaybackThread()
            playback_thread.set_data(binaural_data["audio_data"] if binaural_data["audio_data"] is not None else recording_thread.get_data())
            playback_thread.start()
        except AttributeError:
            interface.audio_manager.playback_state["stopped"] = True
            interface.show_error_message("Record something first.")

    elif interface.audio_manager.playback_state["in_process"]:
        try:
            if playback_thread.done:
                interface.audio_manager.playback_state["terminated"] = True
                playback_thread.done = False
                print("Recording done")
        except AttributeError:
            interface.show_error_message("Record something first.")

    if interface.audio_manager.edit_state["started"]:
        print("Editing started")
        try:
            playback_thread = audio_io.PlaybackThread()
            playback_thread.set_data(recording_thread.get_data())
            playback_thread.start()
        except AttributeError:
            interface.audio_manager.edit_state["stopped"] = True
            interface.show_error_message("Record something first")

    elif interface.audio_manager.edit_state["in_process"]:

        if playback_thread.done:
            interface.audio_manager.edit_state["terminated"] = True
            playback_thread.done = False

    if interface.audio_manager.edit_state["stopped"]:

        filter_data = interface.audio_controller.get_filter_data()

        if len(filter_data) > 0 and recording_thread is not None:
            reverb_data["filter_data"], binaural_data["filter_data"] = audio_processing.unpack_data(recording_thread.get_data(), filter_data)

            reverb_data["audio_data"] = audio_processing.apply_reverb_filtering(recording_thread.get_data(), reverb_data["filter_data"])
            binaural_data["audio_data"] = audio_processing.apply_binaural_filtering(reverb_data["audio_data"], binaural_data["filter_data"])

            interface.audio_controller.clear_filter_data()

    if interface.audio_manager.buttons["open_button"].clicked:

        try:
            audio_data = file_manager.open_file_wav("audio_samples")

            recording_thread = audio_io.RecordingThread()
            recording_thread.set_data(audio_data)

            rec_time = int(audio_data.shape[0] / recording_thread.sampling_freq)

            minutes = f"0{rec_time // 60}" if rec_time // 60 < 10 else f"{rec_time // 60}"
            seconds = f"0{rec_time % 60}" if rec_time % 60 < 10 else f"{rec_time % 60}"

            interface.audio_manager.text_fields["recording_timer"].text = minutes + ":" + seconds

        except (RuntimeError, UnicodeDecodeError):
            interface.show_error_message("Error wrong file type, expected type .wav")
        except FileNotFoundError:
            interface.show_error_message("Error no file found")

    if interface.audio_manager.buttons["save_button"].clicked:
        try:
            file_manager.save_file(reverb_data["audio_data"], binaural_data["filter_data"])
            print("Saved!")
        except AttributeError:
            interface.show_error_message("Record, and play something first")
        except ValueError:
            print("I have no clue, but like stop trying to record a second time will ya?")
