import threading
import sofa
import sounddevice as sd
import numpy as np
import librosa
import serial
from scipy.signal import *

# signal, sampling_freq = librosa.load('../dependencies/impulse_responses/church_balcony.wav', sr=44100)


class AudioIOThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.sampling_freq = 44100
        self.chunk_length = 0.05
        self.chunk_samples = int(self.sampling_freq * self.chunk_length)


class RecordingThread(AudioIOThread):

    def __init__(self):
        super().__init__()
        self.rec_data = np.array([])

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

    def set_data(self, rec_data):
        self.rec_data = rec_data


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
        self.pos_index = 0

        sofa_0_5 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_0_5m.sofa')
        sofa_1 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_1m.sofa')
        sofa_2 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_2m.sofa')
        sofa_3 = sofa.Database.open('../dependencies/impulse_responses/QU_KEMAR_anechoic_3m.sofa')

        self.HR_IR = {0.225: sofa_0_5, 0.55: sofa_1, 0.775: sofa_2, 1: sofa_3}

        self.play_stream = sd.OutputStream(samplerate=self.sampling_freq, channels=2, blocksize=self.chunk_samples,
                                           callback=self.callback)

        self.gyroscope = GyroThread()

    def run(self):
        self.play_stream.start()
        self.gyroscope.run()

    def callback(self, outdata, frames, time, status):

        # The idea here is to get the sample in the middle of the current chunk and find which positional data
        # corresponds to it. That position will be applied to the entire chunk. Say chunk length is 1024, so
        # our reference_sample is 512. If positional data is [(pos info, 500 samples), (different pos info, 400 samples)],
        # then we will apply the second pos info (512 is 12 samples into the second pos) on the entire chunk,
        # simply because it is the most representative of the current chunk.

        reference_sample = self.chunk_index * frames + frames / 2
        elapsed_positional_duration = np.sum(self.positional_data[0:self.pos_index + 1, 2])

        while elapsed_positional_duration < reference_sample and self.pos_index + 1 < len(self.positional_data):
            self.pos_index += 1
            elapsed_positional_duration += self.positional_data[self.pos_index, 2]

        start_index = self.chunk_index * frames
        end_index = (self.chunk_index + 1) * frames

        azimuth_angle = self.positional_data[self.pos_index][0]
        radius = self.positional_data[self.pos_index][1]

        if azimuth_angle == -1:  # don't apply any filters, don't even ask for gyro, output should stay stereo
            outdata[:, 0] = self.play_data[0, start_index:end_index]
            outdata[:, 1] = self.play_data[1, start_index:end_index]
            self.filter_state_unknown = True

        else:

            if self.gyroscope.gyro_connected and self.gyroscope.gyro_is_ready():
                gyro_data = self.gyroscope.get_gyro_data()
                angle = int(abs(azimuth_angle - gyro_data)) if azimuth_angle > gyro_data else int((azimuth_angle + gyro_data) % 360)
            else:
                angle = azimuth_angle

            ir_ear_right = self.HR_IR[radius].Data.IR.get_values(
                indices={"M": angle, "R": 0, "E": 0})
            ir_ear_left = self.HR_IR[radius].Data.IR.get_values(
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

        if self.chunk_index == self.play_data.shape[1] / frames:
            self.play_stream.stop()
            self.gyroscope.close_serial()
            self.done = True

    def set_data(self, play_data, positional_data=None):

        self.play_data = play_data
        self.positional_data = positional_data if positional_data is not None else np.array([-1, 0, len(self.play_data)])


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
