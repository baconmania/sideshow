import win32com.client
import pythoncom
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
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from functools import partial

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
    spectrum_start_color = None
    spectrum_end_color = None
    dark = False

    def __init__(self, lightshow_effect, spectrum_start_color, spectrum_end_color):
        print("__init__ LightShow")
        self.lightshow_effect = lightshow_effect
        self.spectrum_start_color = spectrum_start_color
        self.spectrum_end_color = spectrum_end_color

    def start(self):
        pythoncom.CoInitialize()
        self.prepare_sdk()
        self.prepare_for_animations(self.spectrum_start_color, self.spectrum_end_color)

        while True:
            self.paint()
            self.advance()
            sleep(0)

    def prepare_sdk(self):
        print("Getting SDK handle...")
        aura_sdk = win32com.client.Dispatch("aura.sdk.1")
        print("Got SDK handle %s" % aura_sdk)
        aura_sdk.SwitchMode()

        self.devices = aura_sdk.Enumerate(LedDeviceType.ALL)
        print ("Device Count = " + str(self.devices.Count))
        self.aura_sdk = aura_sdk

    def prepare_for_animations(self, spectrum_start_color, spectrum_end_color):
        self.colors = list(spectrum_start_color.range_to(spectrum_end_color,32))
        self.colors.reverse()
        self.frames_by_led = defaultdict(lambda: defaultdict(list))

        for i in range(0, self.devices.Count):
            if self.devices[i].Type == LedDeviceType.MB_ADDRESABLE:
                print(self.devices[i].Lights.Count) ## There are 120 LEDs total, 10 LEDs per "cable" on the ribbon
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

        return Color('#%s' % hex(reversed)[2:].zfill(6))

    def paint(self):    
        # print('Painting frame %d with actual bytes %s' % (frame, hex(color)))
        for dev in range(0, self.devices.Count):
            device = self.devices[dev]
            # print("LED count: %d" % dev.Lights.Count)

            for i in range(device.Lights.Count):
                if self.dark:
                    color = 0
                else:
                    color = int('ff' + LightShow.reverse_endianness(self.colors[self.frames_by_led[dev][i].frame]).hex_l[1:], 16)
                device.Lights(i).color = color # 0xAABBGGRR

        for dev in range(0, self.devices.Count):
            device = self.devices[dev]
            device.Apply()

    def advance(self):
        if self.dark:
            return
        
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

    def toggle_darkness(self):
        self.dark = not self.dark



def terminate(signalNumber, frame):
    print ('(SIGTERM) terminating the process')
    sys.exit()

def animate(lightshow):
    try:
        print("starting animation")
        lightshow.start()
    except KeyboardInterrupt:
        terminate(None, None)

def serve(lightshow):
    print("Starting server")
    webServer = HTTPServer(("0.0.0.0", 9898), partial(DarknessToggleServer, lightshow))

    try:
        webServer.serve_forever()
        print("Server started")
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")


class DarknessToggleServer(BaseHTTPRequestHandler):
    lightshow = None

    def __init__(self, ):
        self.lightshow = lightshow


    def do_GET(self):
        lightshow.toggle_darkness()
        self.send_response(204)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("ok", "utf-8"))

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, terminate) # this doesn't work anymore
    lightshow = LightShow(ColorTrail(), Color("#006aff"), Color("#9000ff"))
    x = threading.Thread(target=animate, args=[lightshow])
    x.start()
    # server = threading.Thread(target=serve, args=[lightshow])
    # server.start()