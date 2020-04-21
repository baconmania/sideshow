#!python3

import pygame, pigame
from pygame.locals import *
import os
from time import sleep
import RPi.GPIO as GPIO
import MetricsClient
import sys
import logging 
import signal
import time
from svg import Parser, Rasterizer
import traceback
import threading

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
  MARGIN = 20
  OFF_WHITE = (255, 255, 240)

  def __init__(self):
    os.putenv('SDL_VIDEODRV','fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV','dummy')
    os.putenv('SDL_MOUSEDEV','/dev/null')
    os.putenv('DISPLAY','')
    self.running = True

    signal.signal(signal.SIGINT, self.signal_handler)
    signal.signal(signal.SIGTERM, self.signal_handler)

  def signal_handler(self, signal, frame):
    print('Killing...')
    self.metrics_refresher.stop()
    self.running = False
    sys.exit(0)

  def render_cpu_gpu_temps_page(self):
    LARGE_SQUARE_ICON_SIZE = 100
    icon_rect = pygame.Rect(Sideshow.MARGIN, Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (icon_rect.width, icon_rect.height))
    self.lcd.blit(icon_img, icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['cpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(icon_rect.center[0], Sideshow.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    icon_rect = pygame.Rect(Sideshow.SCREEN_WIDTH - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, Sideshow.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    icon_img = pygame.transform.scale(pygame.image.load('resources/gpu_line.png'), (icon_rect.width, icon_rect.height))
    self.lcd.blit(icon_img, icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['gpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(icon_rect.center[0], Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - 40))
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

  def run(self):
    self.metrics_refresher = MetricsRefresher()
    threading.Thread(target=self.metrics_refresher).start()

    pygame.init()
    pitft = pigame.PiTft()

    pygame.mouse.set_visible(True)

    self.lcd = pygame.display.set_mode((Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT))
    self.lcd.fill((0,0,0))
    self.font_big = pygame.font.Font('resources/simplifica.ttf', 120)

    pygame.display.update()

    while self.running:
      try:
        pitft.update()
        
        self.lcd.fill((0,0,0))
        self.render_cpu_gpu_temps_page()

        for event in pygame.event.get():
          if event.type is MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            logger.debug('Touch detected at %s', str(pos))
          elif event.type is MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            logger.debug('UnTouch detected at %s', str(pos))  
            pass
      except Exception as e:
        logger.error(str(e))
        track = traceback.format_exc()
        print(track)
        # Try again after a second
      finally:
        time.sleep(0.1)


def init_logging():
  log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(logging.Formatter(log_format))
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  logger.addHandler(console_handler)
  return logger

print(os.environ)

logger = init_logging()
Sideshow().run()