#!python3

import pygame
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

class MetricsRefresher:
  def __init__(self, pitft):
    self.pitft = pitft
    self.running = True

  def stop(self):
    self.running = False

  def __call__(self):
    while self.running:
      try:
        self.pitft.render_metrics(MetricsClient.get_metrics())
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
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

    self.running = True

    signal.signal(signal.SIGINT, self.signal_handler)
    signal.signal(signal.SIGTERM, self.signal_handler)

  def signal_handler(self, signal, frame):
    print('Killing...')
    self.running = False
    sys.exit(0)

  @staticmethod
  def invert_img(img):
    inv = pygame.Surface(img.get_rect().size, pygame.SRCALPHA)
    inv.fill((255,255,255,255))
    inv.blit(img, (0,0), None, pygame.BLEND_RGB_SUB)
    return inv

  @staticmethod
  def load_svg(filename, scale=None, size=None, clip_from=None, fit_to=None):
    """Returns Pygame Image object from rasterized SVG

    If scale (float) is provided and is not None, image will be scaled.
    If size (w, h tuple) is provided, the image will be clipped to specified size.
    If clip_from (x, y tuple) is provided, the image will be clipped from specified point.
    If fit_to (w, h tuple) is provided, image will be scaled to fit in specified rect.
    """
    svg = Parser.parse_file(filename)
    tx, ty = 0, 0
    if size is None:
        w, h = svg.width, svg.height
    else:
        w, h = size
        if clip_from is not None:
            tx, ty = clip_from
    if fit_to is None:
        if scale is None:
            scale = 1
    else:
        fit_w, fit_h = fit_to
        scale_w = float(fit_w) / svg.width
        scale_h = float(fit_h) / svg.height
        scale = min([scale_h, scale_w])
    rast = Rasterizer()
    req_w = int(w * scale)
    req_h = int(h * scale)
    buff = rast.rasterize(svg, req_w, req_h, scale, tx, ty)
    image = pygame.image.frombuffer(buff, (req_w, req_h), 'ARGB')
    return image

  def render_cpu_gpu_temps_page(self):
    LARGE_SQUARE_ICON_SIZE = 100
    icon_rect = pygame.Rect(Sideshow.MARGIN, Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (icon_rect.width, icon_rect.height))
    self.lcd.blit(icon_img, icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics['temps']['cpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(icon_rect.center[0], Sideshow.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    icon_rect = pygame.Rect(Sideshow.SCREEN_WIDTH - Sideshow.MARGIN - LARGE_SQUARE_ICON_SIZE, Sideshow.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    icon_img = pygame.transform.scale(pygame.image.load('resources/gpu_line.png'), (icon_rect.width, icon_rect.height))
    self.lcd.blit(icon_img, icon_rect)

    text_surface = self.font_big.render('%s°' % self.metrics['temps']['gpu'], True, Sideshow.OFF_WHITE)
    rect = text_surface.get_rect(center=(icon_rect.center[0], Sideshow.SCREEN_HEIGHT - Sideshow.MARGIN - 40))
    self.lcd.blit(text_surface, rect)

    pygame.display.update()

  def run(self):
    pygame.init()
    self.font_big = pygame.font.Font('resources/simplifica.ttf', 120)

    pygame.mouse.set_visible(False)
    self.lcd = pygame.display.set_mode((Sideshow.SCREEN_WIDTH, Sideshow.SCREEN_HEIGHT))
    self.lcd.fill((0,0,0))
    pygame.display.update()

    while self.running:
      try:
        self.metrics = MetricsClient.get_metrics()
        
        self.lcd.fill((0,0,0))
        self.render_cpu_gpu_temps_page()

      except Exception as e:
        logger.error(str(e))
        track = traceback.format_exc()
        print(track)
        # Try again after a second
      finally:
        time.sleep(1)


def init_logging():
  log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(logging.Formatter(log_format))
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)
  logger.addHandler(console_handler)
  return logger

logger = init_logging()
Sideshow().run()