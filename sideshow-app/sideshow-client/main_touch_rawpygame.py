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
from abc import ABC, abstractmethod

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

class SideshowPage(ABC):
  MARGIN = 20
  OFF_WHITE = (255, 255, 240)
  BLACK = (0, 0, 0)

  def __init__(self, lcd, touch_targets, latest_metrics):
    self.lcd = lcd
    self.touch_targets = touch_targets
    self.latest_metrics = latest_metrics
    self.font_big = pygame.font.Font('resources/simplifica.ttf', 120)

  def render_page(self):
    pass

class SideshowDetailPage(SideshowPage):
  def __init__(self, lcd, touch_targets, latest_metrics):
    super().__init__(lcd, touch_targets, latest_metrics)

  @abstractmethod
  def render_detail_page(self):
    pass

  def render_page(self):
    self.render_back_button()
    self.render_detail_page()

  def render_back_button(self):
    back_button_img = pygame.image.load('resources/back.png')
    back_button_touch_target = back_button_img.get_rect(left=0, top=0, width=100, height=100)
    self.touch_targets['BACK_BUTTON'] = back_button_touch_target
    back_button_rect = back_button_img.get_rect(left=SideshowPage.MARGIN, top=SideshowPage.MARGIN)
    self.lcd.blit(back_button_img, back_button_rect)

class CpuDetailPage(SideshowDetailPage):
  def __init__(self, lcd, touch_targets, latest_metrics):
    super().__init__(lcd, touch_targets, latest_metrics)

  def render_detail_page(self):
    self.render_back_button()

    icon_img = pygame.image.load('resources/cpu_line_250.png')
    gpu_icon_rect = icon_img.get_rect(center=(50, Sideshow.SCREEN_HEIGHT - 50))
    Sideshow.blit_alpha(self.lcd, icon_img, (gpu_icon_rect.x, gpu_icon_rect.y), .28)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['cpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(left=SideshowPage.MARGIN, bottom=Sideshow.SCREEN_HEIGHT)
    self.lcd.blit(text_surface, rect)

    pygame.display.update()
  
class GpuDetailPage(SideshowDetailPage):
  def __init__(self, lcd, touch_targets, latest_metrics):
    super().__init__(lcd, touch_targets, latest_metrics)

  def render_detail_page(self):
    self.touch_targets = {}
    self.render_back_button()

    icon_img = pygame.image.load('resources/gpu_line_250.png')
    gpu_icon_rect = icon_img.get_rect(center=(50, Sideshow.SCREEN_HEIGHT - 90))
    Sideshow.blit_alpha(self.lcd, icon_img, (gpu_icon_rect.x, gpu_icon_rect.y), .28)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['gpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(left=SideshowPage.MARGIN, bottom=Sideshow.SCREEN_HEIGHT)
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

class HomePage(SideshowPage):
  def __init__(self, lcd, touch_targets, latest_metrics):
    super().__init__(lcd, touch_targets, latest_metrics)

  def render_page(self):
    LARGE_SQUARE_ICON_SIZE = 100
    cpu_icon_rect = pygame.Rect(SideshowPage.MARGIN, Sideshow.SCREEN_HEIGHT - SideshowPage.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['CPU_ICON'] = cpu_icon_rect
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (cpu_icon_rect.width, cpu_icon_rect.height))
    self.lcd.blit(icon_img, cpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['cpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(center=(cpu_icon_rect.center[0], SideshowPage.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    gpu_icon_rect = pygame.Rect(Sideshow.SCREEN_WIDTH - SideshowPage.MARGIN - LARGE_SQUARE_ICON_SIZE, SideshowPage.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['GPU_ICON'] = gpu_icon_rect
    icon_img = pygame.image.load('resources/gpu_line.png')
    self.lcd.blit(icon_img, gpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['gpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(center=(gpu_icon_rect.center[0], Sideshow.SCREEN_HEIGHT - SideshowPage.MARGIN - 40))
    self.lcd.blit(text_surface, rect)


class Sideshow():
  SCREEN_WIDTH = 320
  SCREEN_HEIGHT = 240

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

  @staticmethod
  def blit_alpha(target, source, location, opacity_factor):
        x = location[0]
        y = location[1]
        temp = pygame.Surface((source.get_width(), source.get_height())).convert()
        temp.blit(target, (-x, -y))
        temp.blit(source, (0, 0))
        temp.set_alpha(255 * opacity_factor)
        target.blit(temp, location)

  def render_current_page(self):
    self.touch_targets = {}
    try:
      {
        'CPU_PAGE': CpuDetailPage,
        'GPU_PAGE': GpuDetailPage,
        'HOME': HomePage
      }[self.current_page](self.lcd, self.touch_targets, self.metrics_refresher.latest_metrics).render_page()
    except KeyError:
      HomePage().render_page()
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
            pos = pygame.mouse.get_pos()
            logger.debug('UnTouch detected at %s', str(pos))  
            touched_target = self.get_touched_target(pos)

            logger.debug('Touched target was %s' % touched_target)

            if touched_target is not None:
              self.current_page = self.get_page_for_touch_target(touched_target)

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