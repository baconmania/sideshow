import win32com.client
import signal
from enum import IntEnum
from time import sleep
import sys
from colour import Color
import re
from collections import defaultdict
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
devices = auraSdk.Enumerate(LedDeviceType.DRAM_RGB)

frame = 0
frames_by_led = defaultdict(lambda: defaultdict(list))

for i in range(0, devices.Count):
    for j in range(0, devices[0].Lights.Count):
        frames_by_led[i][j] = 0

def flip_bits(color):
    matches = re.fullmatch(r'#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})', color.hex_l)
    return Color('#%s%s%s' % (matches.group(3), matches.group(2), matches.group(1)))
    # colors[frame].hex_l[1:]

def paint():    
    # print('Painting frame %d with actual bytes %s' % (frame, hex(color)))

    # print("Painting %s" % hex(color))

    # print(dir(devices))

    for dev in range(0, devices.Count):
        device = devices[dev]
        # print(dir(dev))
        # print("LED count: %d" % dev.Lights.Count)

        for i in range(device.Lights.Count):
            color = int('ff' + flip_bits(colors[frames_by_led[dev][i]]).hex_l[1:], 16)
            device.Lights(i).color = color # 0xAABBGGRR

        # if dev.Type == LedDeviceType.DRAM_RGB:
        #     print([method_name for method_name in dir(dev)
        #               if callable(getattr(dev, method_name))])

        device.Apply()

def advance():
    for i in range(0, devices.Count):
        for j in range(0, devices[0].Lights.Count):
            frames_by_led[i][j] = (frames_by_led[i][j] + 1) % len(colors)


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
    advance()
    # sleep(0.001)
