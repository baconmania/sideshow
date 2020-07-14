import win32com.client
import signal
from enum import IntEnum
from time import sleep
import sys
from colour import Color
import re

running = True

def terminateProcess(signalNumber, frame):
    print ('(SIGTERM) terminating the process')
    running = False
    sys.exit()

class LedDeviceType(IntEnum):
    ALL = 0
    MB_RGB = 0x10000
    MB_ADDRESABLE = 0x11000
    DESKTOP_RGB = 0x12000
    VGA_RGB = 0x20000
    DISPLAY_RGB = 0x30000
    HEADSET_RGB = 0x40000
    MICROPHONE_RGB = 0x50000
    EXTERNAL_HARD_DRIVER_RGB = 0x60000
    EXTERNAL_BLUE_RAY_RGB = 0x61000
    DRAM_RGB = 0x70000
    KEYBOARD_RGB = 0x80000
    NB_KB_RGB = 0x81000
    NB_KB_4ZONE_RGB = 0x81001
    MOUSE_RGB = 0x90000
    CHASSIS_RGB = 0xB0000
    PROJECTOR_RGB = 0xC0000

################## main script #####################
print("starting")
auraSdk = win32com.client.Dispatch("aura.sdk.1")
auraSdk.SwitchMode()

# print ("Device Count = " + str(devices.Count))

signal.signal(signal.SIGTERM, terminateProcess)

colors = list(Color("#00a6ff").range_to(Color("#5500ff"),50))

frame = 0

def flip_bits(color):
    matches = re.fullmatch(r'#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})', color.hex_l)
    return Color('#%s%s%s' % (matches.group(3), matches.group(2), matches.group(1)))
    # colors[frame].hex_l[1:]

def paint():
    color = int('ff' + flip_bits(colors[frame]).hex_l[1:], 16)
    # print('Painting frame %d with actual bytes %s' % (frame, hex(color)))

    # print("Painting %s" % hex(color))
    devices = auraSdk.Enumerate(LedDeviceType.ALL)
    for dev in devices:
        # print(dir(dev))
        # print("LED count: %d" % dev.Lights.Count)

        for i in range(dev.Lights.Count):
            dev.Lights(i).color = color # 0xAABBGGRR

        # if dev.Type == LedDeviceType.DRAM_RGB:
        #     print([method_name for method_name in dir(dev)
        #               if callable(getattr(dev, method_name))])

        dev.Apply()


forward = True
while True and running:
    paint()
    if forward:
        frame += 1
    else:
        frame -= 1

    if frame >= len(colors):
        forward = False
        frame = len(colors) - 1

    if frame <= 0:
        forward = True
        frame = 0
    # sleep(0.001)
