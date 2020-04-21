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
  BLACK = (0, 0, 0)

  def __init__(self):
    os.putenv('SDL_VIDEODRV','fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV','dummy')
    os.putenv('SDL_MOUSEDEV','/dev/null')
    os.putenv('DISPLAY','')
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
    try:
      {
        'CPU_PAGE': self.render_cpu_page,
        'GPU_PAGE': self.render_gpu_page,
        'HOME': self.render_home_page
      }[self.current_page]()
    except KeyError:
      self.render_home_page()

  def render_cpu_page(self):
    back_button_img = pygame.image.load('resources/back.png')
    back_button_rect = back_button_img.get_rect(left=Sideshow.MARGIN, top=Sideshow.MARGIN)
    self.touch_targets['BACK_BUTTON'] = back_button_rect
    self.lcd.blit(back_button_img, back_button_rect) 

    LARGE_SQUARE_ICON_SIZE = 100
    cpu_icon_rect = pygame.Rect(Sideshow.MARGIN, Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['CPU_ICON'] = cpu_icon_rect
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (cpu_icon_rect.width, cpu_icon_rect.height))
    self.lcd.blit(icon_img, cpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['cpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(cpu_icon_rect.center[0], Sideshow.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

  def render_gpu_page(self):
    back_button_img = pygame.image.load('resources/back.png')
    back_button_touch_target = back_button_img.get_rect(left=0, top=0, width=50, height=50)
    self.touch_targets['BACK_BUTTON'] = back_button_touch_target
    back_button_rect = back_button_img.get_rect(left=Sideshow.MARGIN, top=Sideshow.MARGIN)
    self.lcd.blit(back_button_img, back_button_rect) 

    LARGE_SQUARE_ICON_SIZE = 100

    gpu_icon_rect = pygame.Rect(Sideshow.SCREEN_WIDTH - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, Sideshow.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['GPU_ICON'] = gpu_icon_rect
    icon_img = pygame.image.load('resources/gpu_line.png')
    self.lcd.blit(icon_img, gpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['gpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(gpu_icon_rect.center[0], Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - 40))
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

  def render_home_page(self):
    LARGE_SQUARE_ICON_SIZE = 100
    cpu_icon_rect = pygame.Rect(Sideshow.MARGIN, Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['CPU_ICON'] = cpu_icon_rect
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (cpu_icon_rect.width, cpu_icon_rect.height))
    self.lcd.blit(icon_img, cpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['cpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(cpu_icon_rect.center[0], Sideshow.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    gpu_icon_rect = pygame.Rect(Sideshow.SCREEN_WIDTH - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, Sideshow.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['GPU_ICON'] = gpu_icon_rect
    icon_img = pygame.image.load('resources/gpu_line.png')
    self.lcd.blit(icon_img, gpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics_refresher.latest_metrics['temps']['gpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(gpu_icon_rect.center[0], Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - 40))
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

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
    pitft = pigame.PiTft()

    pygame.mouse.set_visible(True)

    self.lcd = pygame.display.set_mode((Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT))
    self.lcd.fill(Sideshow.BLACK)
    self.font_big = pygame.font.Font('resources/simplifica.ttf', 120)

    pygame.display.update()

    while self.running:
      try:
        pitft.update()

        for event in pygame.event.get():
          if event.type is MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            logger.debug('Touch detected at %s', str(pos))
          elif event.type is MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            logger.debug('UnTouch detected at %s', str(pos))  
            touched_target = self.get_touched_target(pos)

            logger.debug('Touched target was %s' % touched_target)

            if touched_target is not None:
              self.current_page = self.get_page_for_touch_target(touched_target)

        self.lcd.fill(Sideshow.BLACK)
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