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
        time.sleep(1)

class Sideshow():
  SCREEN_WIDTH = 320
  SCREEN_HEIGHT = 240

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

  def run(self):
    self.metrics_refresher = MetricsRefresher()
    threading.Thread(target=self.metrics_refresher).start()

    pygame.init()

    pygame.time.set_timer(USEREVENT+1, 30 * 1000)

    pitft = pigame.PiTft()

    pygame.mouse.set_visible(False)

    self.lcd = pygame.display.set_mode((Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT))
    self.lcd.fill(SideshowPage.BLACK)

    pygame.display.update()

    while self.running:
      try:
        pitft.update()

        for event in pygame.event.get():
          if event.type is MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            logger.debug('Touch detected at %s', str(pos))
          elif event.type is MOUSEBUTTONUP:
            self.last_touch_epoch_millis = int(round(time.time() * 1000))
            pos = pygame.mouse.get_pos()
            logger.debug('UnTouch detected at %s', str(pos))  
            touched_target = self.get_touched_target(pos)

            logger.debug('Touched target was %s' % touched_target)

            if touched_target is not None:
              if touched_target in ['CPU_ICON', 'GPU_ICON']:
                self.enable_carousel = False
              elif touched_target is 'BACK_BUTTON':
                self.enable_carousel = True

              self.current_page = self.get_page_for_touch_target(touched_target)
          elif event.type is USEREVENT+1 and self.enable_carousel and int(round(time.time() * 1000)) - self.last_touch_epoch_millis >= 30 * 1000:
            self.current_page = random.choice(['CPU_PAGE', 'GPU_PAGE', 'HOME'])

        self.lcd.fill(SideshowPage.BLACK)
        self.render_current_page()
      except Exception as e:
        logger.error(str(e))
        trace = traceback.format_exc()
        print(trace)
        # Try again after a second
      finally:
        time.sleep(0.1)


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