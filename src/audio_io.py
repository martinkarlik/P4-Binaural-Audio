import threading
import sofa
import sounddevice as sd
import numpy as np
import librosa
import serial
from scipy.signal import *

# signal, sampling_freq = librosa.load('../dependencies/impulse_responses/church_balcony.wav', sr=44100)
# signal = np.reshape(signal, (-1, 1))
# hrtf_database = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
# ir_ear1 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 0, "E": 0})
# ir_ear2 = hrtf_database.Data.IR.get_values(indices={"M": 1, "R": 1, "E": 0})


class AudioIOThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_freq = 44100
        self.chunk_length = 0.05
        self.chunk_samples = int(self.sampling_freq * self.chunk_length)


class RecordingThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.rec_data = np.array([[]])

        self.rec_stream = sd.InputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                         callback=self.callback)

    def callback(self, indata, frames, time, status):

        if self.rec_data.size == 0:
            self.rec_data = indata
        else:
            self.rec_data = np.append(self.rec_data, indata, axis=0)

    def run(self):
        self.rec_stream.start()

    def stop(self):
        self.rec_stream.stop()
        self.rec_data = np.array(self.rec_data)

    def get_data(self):
        return self.rec_data


class PlaybackThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.play_data = np.array([])
        self.done = False

    def run(self):
        sd.play(self.play_data)
        sd.wait()
        self.done = True

    def set_data(self, play_data):
        self.play_data = play_data


class DynamicPlaybackThread(PlaybackThread):

    def __init__(self):
        super().__init__()
        self.play_data = np.array([])
        self.positional_data = np.array([])

        self.filter_state_right = np.zeros(2047)
        self.filter_state_left = np.zeros(2047)
        self.filter_state_unknown = True

        self.chunk_index = 0

        sofa_0_5 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_0_5m.sofa')
        sofa_1 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
        sofa_2 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_2m.sofa')
        sofa_3 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_3m.sofa')

        self.hrtf_database = {0.2: sofa_0_5, 0.4: sofa_1, 0.8: sofa_2, 1.2: sofa_3}

        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                           callback=self.callback)

        self.gyroscope = GyroThread()

    def run(self):
        self.play_stream.start()
        self.gyroscope.run()

    def callback(self, outdata, frames, time, status):
        if self.gyroscope.gyro_is_ready() and self.gyroscope.gyro_connected:
            corresponding_sample = self.chunk_index * frames + frames / 2

            elapsed_samples = self.positional_data[0][2]
            pos_index = 0
            while elapsed_samples < corresponding_sample:
                pos_index += 1
                elapsed_samples += self.positional_data[pos_index][2]

            angle = self.positional_data[pos_index][0]
            radius = self.positional_data[pos_index][1]

            start_index = self.chunk_index * frames
            end_index = (self.chunk_index + 1) * frames

            gyro_data = self.gyroscope.get_gyro_data()
            print("gotten: ", gyro_data)

            if angle == -1:  # don't apply any filters, output should stay stereo
                outdata[:, 0] = self.play_data[0, start_index:end_index]
                outdata[:, 1] = self.play_data[1, start_index:end_index]
                self.filter_state_unknown = True
            else:
                if angle > gyro_data:
                    ir_ear_right = self.hrtf_database[radius].Data.IR.get_values(
                        indices={"M": int(abs(angle - gyro_data)), "R": 0, "E": 0})
                    ir_ear_left = self.hrtf_database[radius].Data.IR.get_values(
                        indices={"M": int(abs(angle - gyro_data)), "R": 1, "E": 0})
                else:
                    ir_ear_right = self.hrtf_database[radius].Data.IR.get_values(
                        indices={"M": int((angle + gyro_data) % 360), "R": 0, "E": 0})
                    ir_ear_left = self.hrtf_database[radius].Data.IR.get_values(
                        indices={"M": int((angle + gyro_data) % 360), "R": 1, "E": 0})

                if self.filter_state_unknown:
                    self.filter_state_right = np.zeros(2047)
                    self.filter_state_left = np.zeros(2047)
                    self.filter_state_unknown = False

                outdata[:, 0], self.filter_state_right = \
                    lfilter(ir_ear_right, 1, self.play_data[0, start_index:end_index], zi=self.filter_state_right)
                outdata[:, 1], self.filter_state_left = \
                    lfilter(ir_ear_left, 1, self.play_data[1, start_index:end_index], zi=self.filter_state_left)

            self.chunk_index += 1

            if self.chunk_index + 1 == len(self.play_data) / frames:
                self.play_stream.stop()
                self.gyroscope.close_serial()
                self.done = True
                print("stopped")
        else:
            print("playing without gyro")
            corresponding_sample = self.chunk_index * frames + frames / 2
            elapsed_samples = self.positional_data[0][2]
            pos_index = 0
            while elapsed_samples < corresponding_sample:
                pos_index += 1
                elapsed_samples += self.positional_data[pos_index][2]

            angle = self.positional_data[pos_index][0]
            radius = self.positional_data[pos_index][1]

            start_index = self.chunk_index * frames
            end_index = (self.chunk_index + 1) * frames

            if angle == -1:  # don't apply any filters, output should stay stereo
                outdata[:, 0] = self.play_data[0, start_index:end_index]
                outdata[:, 1] = self.play_data[1, start_index:end_index]
                self.filter_state_unknown = True
            else:
                ir_ear_right = self.hrtf_database[radius].Data.IR.get_values(
                    indices={"M": angle, "R": 0, "E": 0})
                ir_ear_left = self.hrtf_database[radius].Data.IR.get_values(
                    indices={"M": angle, "R": 1, "E": 0})

                if self.filter_state_unknown:
                    self.filter_state_right = np.zeros(2047)
                    self.filter_state_left = np.zeros(2047)
                    self.filter_state_unknown = False

                outdata[:, 0], self.filter_state_right = \
                    lfilter(ir_ear_right, 1, self.play_data[0, start_index:end_index], zi=self.filter_state_right)
                outdata[:, 1], self.filter_state_left = \
                    lfilter(ir_ear_left, 1, self.play_data[1, start_index:end_index], zi=self.filter_state_left)

            self.chunk_index += 1

            if self.chunk_index + 1 == len(self.play_data) / frames:
                self.play_stream.stop()
                self.done = True
                print("stopped without gyro")

    def set_data(self, play_data, positional_data=None):

        self.play_data = play_data
        self.positional_data = positional_data


class GyroThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.received = []
        self.gyro_rotation = 0
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port = 'COM3'
        self.gyro_connected = True

    def run(self):
        try:
            self.ser.open()
            while self.ser.is_open:
                line = self.ser.readline().decode()

                # the third message, (0,1,2), is waiting for the arduino to receive a message so we send it
                if len(self.received) == 3:
                    # Send a signal to the arduino to get the gyroscope to work
                    self.ser.write(str.encode(" "))

                # waiting for the gyroscope to be ready
                if len(self.received) < 8:
                    # time.sleep(1)
                    # The first 3 messages are useless since it is just setup.
                    self.received.append(line)
                    print("Hang tight almost there!")
                elif len(self.received) == 8:
                    # Now print the gyro values, or store it in a value
                    gyro = int(line)
                    if gyro < 0:
                        gyro += 360
                    gyro = (180 + gyro) % 360
                    self.gyro_rotation = gyro
        except serial.serialutil.SerialException:
            self.gyro_connected = False

    def get_gyro_data(self):
        return self.gyro_rotation

    def gyro_is_ready(self):
        return len(self.received) == 8

    def close_serial(self):
        self.ser.close()
