import win32com.client
import signal
from enum import IntEnum
from enum import Enum
from time import sleep
import sys
from colour import Color
import re
from collections import defaultdict
from lightshow_common import AnimationDirection, LedAnimationState
from LightShowEffects import UpwardScroll, ColorTrail, Shimmer


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

class LightShow():
    aura_sdk = None
    devices = []
    colors = []
    frames_by_led = None
    lightshow_effect = None

    def __init__(self, spectrum_start_color, spectrum_end_color, lightshow_effect):
        self.lightshow_effect = lightshow_effect

        self.prepare_sdk()
        self.prepare_for_animations(spectrum_start_color, spectrum_end_color)

    def start(self):
        while True:
            self.paint()
            self.advance()

    def prepare_sdk(self):
        aura_sdk = win32com.client.Dispatch("aura.sdk.1")
        aura_sdk.SwitchMode()

        self.devices = aura_sdk.Enumerate(LedDeviceType.ALL)
        print ("Device Count = " + str(self.devices.Count))
        self.aura_sdk = aura_sdk

    def prepare_for_animations(self, spectrum_start_color, spectrum_end_color):
        self.colors = list(spectrum_start_color.range_to(spectrum_end_color,20))
        self.colors.reverse()
        self.frames_by_led = defaultdict(lambda: defaultdict(list))

        for i in range(0, self.devices.Count):
            for j in range(0, self.devices[i].Lights.Count):
                self.frames_by_led[i][j] = self.lightshow_effect.set_initial_state_for_led(i, j, self.colors)

    @staticmethod
    def reverse_endianness(color):
        """Convert a 0xRRGGBB color to a 0xBBGGRR value"""
        original = int(color.hex_l[1:], 16)
        reversed = 0

        blue_shifted = (0x0000ff & original) << 16
        green = (0x00ff00 & original)
        red_shifted = (0xff0000 & original) >> 16

        reversed |= blue_shifted
        reversed |= green
        reversed |= red_shifted
        return Color('#%s' % hex(reversed)[2:])

    def paint(self):    
        # print('Painting frame %d with actual bytes %s' % (frame, hex(color)))
        for dev in range(0, self.devices.Count):
            device = self.devices[dev]
            # print("LED count: %d" % dev.Lights.Count)

            for i in range(device.Lights.Count):
                color = int('ff' + LightShow.reverse_endianness(self.colors[self.frames_by_led[dev][i].frame]).hex_l[1:], 16)
                device.Lights(i).color = color # 0xAABBGGRR

            device.Apply()

    def advance(self):
        for i in range(0, self.devices.Count):
            for j in range(0, self.devices[i].Lights.Count):
                if self.frames_by_led[i][j].direction == AnimationDirection.FORWARD:
                    new_frame = (self.frames_by_led[i][j].frame + 1)
                    if new_frame >= len(self.colors):
                        new_frame = len(self.colors) - 1
                        direction = AnimationDirection.REVERSE
                    else:
                        direction = AnimationDirection.FORWARD
                else:
                    new_frame = (self.frames_by_led[i][j].frame - 1)
                    if new_frame <= 0:
                        new_frame = 0
                        direction = AnimationDirection.FORWARD
                    else:
                        direction = AnimationDirection.REVERSE

                self.frames_by_led[i][j] = LedAnimationState(new_frame, direction)



def terminate(signalNumber, frame):
    print ('(SIGTERM) terminating the process')
    sys.exit()

def main():
    try:
        print("starting")
        signal.signal(signal.SIGTERM, terminate)
        LightShow(Color("#00a6ff"), Color("#5500ff"), ColorTrail()).start()
    except KeyboardInterrupt:
        terminate(None, None)

if __name__ == '__main__':
    main()