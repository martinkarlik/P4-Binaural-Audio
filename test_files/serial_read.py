import serial
import time

received = []
gyro_rotation = 0
sent = False

ser = serial.Serial()
ser.baudrate = 115200
ser.port = 'COM3'
ser.open()
# print(ser.name)

# time.sleep(2)
# ser.write(str.encode(" "))


while ser.is_open:
    line = ser.readline().decode()
    # print(line)

    # waiting for the gyroscope to be ready
    if len(received) < 8:
        # time.sleep(1)
        # The first 3 messages are useless since it is just setup.
        received.append(line)
    elif len(received) == 8:
        # Now print the gyro values, or store it in a value 
        gyro_rotation = int(line)

    # the third message, (0,1,2), is waiting for the arduino to receive a message so we send it
    if len(received) == 3:
        # Send a signal to the arduino to get the gyroscope to work
        ser.write(str.encode(" "))