#!python3

import os
import sys
import logging
import signal
import time
import traceback
import threading
import pygame, pigame
import random
from pygame.locals import *
import RPi.GPIO as GPIO
import requests
import MetricsClient
from pages import SideshowPage, SideshowDetailPage, HomePage, GpuDetailPage, CpuDetailPage

class MetricsRefresher:
  def __init__(self):
    self.running = True
    self.latest_metrics = {}

  def stop(self):
    self.running = False

  def __call__(self):
    while self.running:
      try:
        self.latest_metrics = MetricsClient.get_metrics()
      except Exception as e:
        logger.error(str(e))
        # Try again after a second
      finally:
        time.sleep(1.0)

class Sideshow():
  SCREEN_WIDTH = 320
  SCREEN_HEIGHT = 240
  CUSTOM_EVENT_ADVANCE_CAROUSEL = pygame.USEREVENT + 1

  def __init__(self):
    os.putenv('SDL_VIDEODRV','fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV','dummy')
    os.putenv('SDL_MOUSEDEV','/dev/null')
    os.putenv('DISPLAY','')
    self.last_touch_epoch_millis = 0
    self.enable_carousel = True
    self.running = True
    self.current_page = 'HOME'
    self.touch_targets = {}

    signal.signal(signal.SIGINT, self.signal_handler)
    signal.signal(signal.SIGTERM, self.signal_handler)

  def signal_handler(self, signal, frame):
    print('Killing...')
    self.metrics_refresher.stop()
    self.running = False
    sys.exit(0)

  def render_current_page(self):
    self.lcd.fill(SideshowPage.BLACK)
    self.touch_targets = {}

    try:
      {
        'CPU_PAGE': CpuDetailPage,
        'GPU_PAGE': GpuDetailPage,
        'HOME': HomePage
      }[self.current_page](self.lcd, self.touch_targets, self.metrics_refresher.latest_metrics, (Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT)).render()
    except KeyError:
      HomePage(self.lcd, self.touch_targets, self.metrics_refresher.latest_metrics, (Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT)).render()

  def get_touched_target(self, touch_pos):
    for (touch_target_id, touch_target_rect) in self.touch_targets.items():
      logger.debug('Checking if touch at %s collides with Rect %s', touch_pos, touch_target_rect)
      if touch_target_rect.collidepoint(touch_pos):
        return touch_target_id

    return None

  def get_page_for_touch_target(self, touch_target_id):
    try:
      return {
        'CPU_ICON': 'CPU_PAGE',
        'GPU_ICON': 'GPU_PAGE',
        'BACK_BUTTON': 'HOME'
      }[touch_target_id]
    except KeyError:
      return self.current_page

  def handle_touch(self):
    pos = pygame.mouse.get_pos()
    logger.debug('Touch detected at %s', str(pos))
    self.last_touch_epoch_millis = int(round(time.time() * 1000))
    touched_target = self.get_touched_target(pos)

    logger.debug('Touched target was %s' % touched_target)

    if touched_target is not None:
      if touched_target in ['CPU_ICON', 'GPU_ICON']:
        self.enable_carousel = False
      elif touched_target is 'BACK_BUTTON':
        self.enable_carousel = True

    self.current_page = self.get_page_for_touch_target(touched_target)

  def advance_carousel(self):
    if self.enable_carousel and int(round(time.time() * 1000)) - self.last_touch_epoch_millis >= 30 * 1000:
      self.current_page = random.choice(['CPU_PAGE', 'GPU_PAGE', 'HOME'])

  def init_metrics_refresher(self):
    self.metrics_refresher = MetricsRefresher()
    metrics_refresher_thread = threading.Thread(target=self.metrics_refresher)
    metrics_refresher_thread.daemon = True
    metrics_refresher_thread.start()

  def init_button_listener(self):
    self.button_listener = ButtonListener()
    button_listener_thread = threading.Thread(target=self.button_listener)
    button_listener_thread.daemon = True
    button_listener_thread.start()

  def init_pygame(self):
    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.time.set_timer(Sideshow.CUSTOM_EVENT_ADVANCE_CAROUSEL, 30 * 1000)

  def init_touchscreen(self):
    self.lcd = pygame.display.set_mode((Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT))
    self.pitft = pigame.PiTft()

  def handle_pygame_event(self, event):
    if event.type is pygame.MOUSEBUTTONDOWN:
      self.handle_touch()
    elif event.type is Sideshow.CUSTOM_EVENT_ADVANCE_CAROUSEL:
      self.advance_carousel()

  def run(self):
    self.init_metrics_refresher()
    self.init_button_listener()
    self.init_pygame()
    self.init_touchscreen()

    while self.running:
      try:
        self.pitft.update()

        for event in pygame.event.get():
          self.handle_pygame_event(event)

        self.render_current_page()
      except Exception as e:
        logger.error(str(e))
        trace = traceback.format_exc()
        print(trace)
        # Try again after a second
      finally:
        time.sleep(0.05)

class ButtonListener():
  PRESSED = False
  UNPRESSED = True

  pins = {
    'BTN_0': 27,
    'BTN_1': 23,
    'BTN_2': 22,
    'BTN_3': 17,
  }

  handlers = {
    pins['BTN_0']: lambda : requests.get('http://baconmania.cc:9898/'),
    pins['BTN_1']: None,
    pins['BTN_2']: None,
    pins['BTN_3']: None,
  }

  def __init__(self):
    self.last_press_event_fired = {
      ButtonListener.pins['BTN_0']: None,
      ButtonListener.pins['BTN_1']: None,
      ButtonListener.pins['BTN_2']: None,
      ButtonListener.pins['BTN_3']: None,
    }

  def __call__(self):
    self.listen()

  def is_pressed(self, pin):
    return GPIO.input(pin) == ButtonListener.PRESSED

  def is_valid_press(self, pin):
    return (self.last_press_event_fired[pin] is None or time.time() - self.last_press_event_fired[pin] > 1)

  def listen(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ButtonListener.pins['BTN_0'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonListener.pins['BTN_1'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonListener.pins['BTN_2'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ButtonListener.pins['BTN_3'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while True:
      pressed_button_pins = [ pin for pin in ButtonListener.pins.values() if self.is_pressed(pin) ]
      valid_pressed_button_pins = [ pin for pin in pressed_button_pins if self.is_valid_press(pin) ]

      for pin in valid_pressed_button_pins:
        self.last_press_event_fired[pin] = time.time()

      for pin in valid_pressed_button_pins:
        if ButtonListener.handlers[pin] is not None:
          ButtonListener.handlers[pin]()


def init_logging():
  log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(logging.Formatter(log_format))
  logger = logging.getLogger()
  logging.getLogger('urllib3.connectionpool').setLevel(logging.WARN)
  logger.setLevel(logging.DEBUG)
  logger.addHandler(console_handler)
  return logger


logger = init_logging()
Sideshow().run()