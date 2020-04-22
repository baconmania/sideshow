from abc import ABC, abstractmethod
import pygame

class SideshowPage(ABC):
  MARGIN = 20
  OFF_WHITE = (255, 255, 240)
  BLACK = (0, 0, 0)

  def __init__(self, lcd, touch_targets, latest_metrics, screen_dimensions):
    self.lcd = lcd
    self.touch_targets = touch_targets
    self.latest_metrics = latest_metrics
    self.font_big = pygame.font.Font('resources/simplifica.ttf', 120)
    self.font_small = pygame.font.Font('resources/simplifica.ttf', 30)
    self.screen_width = screen_dimensions[0]
    self.screen_height = screen_dimensions[1]

  def render(self):
    self.lcd.fill(SideshowPage.BLACK)
    self.render_page()
    pygame.display.update()

  @abstractmethod
  def render_page(self):
    pass

  @staticmethod
  def blit_alpha(target, source, location, opacity_factor):
    x = location[0]
    y = location[1]
    temp = pygame.Surface((source.get_width(), source.get_height())).convert()
    temp.blit(target, (-x, -y))
    temp.blit(source, (0, 0))
    temp.set_alpha(255 * opacity_factor)
    target.blit(temp, location)


class HomePage(SideshowPage):
  def __init__(self, lcd, touch_targets, latest_metrics, screen_dimensions):
    super().__init__(lcd, touch_targets, latest_metrics, screen_dimensions)

  def render_page(self):
    LARGE_SQUARE_ICON_SIZE = 100
    cpu_icon_rect = pygame.Rect(SideshowPage.MARGIN, self.screen_height - SideshowPage.MARGIN - LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['CPU_ICON'] = cpu_icon_rect
    icon_img = pygame.transform.scale(pygame.image.load('resources/cpu_line.png'), (cpu_icon_rect.width, cpu_icon_rect.height))
    self.lcd.blit(icon_img, cpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['cpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(center=(cpu_icon_rect.center[0], SideshowPage.MARGIN + 55))
    self.lcd.blit(text_surface, rect)

    gpu_icon_rect = pygame.Rect(self.screen_width - SideshowPage.MARGIN - LARGE_SQUARE_ICON_SIZE, SideshowPage.MARGIN - 5, LARGE_SQUARE_ICON_SIZE, LARGE_SQUARE_ICON_SIZE)
    self.touch_targets['GPU_ICON'] = gpu_icon_rect
    icon_img = pygame.image.load('resources/gpu_line.png')
    self.lcd.blit(icon_img, gpu_icon_rect)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['gpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(center=(gpu_icon_rect.center[0], self.screen_height - SideshowPage.MARGIN - 40))
    self.lcd.blit(text_surface, rect)


class SideshowDetailPage(SideshowPage):
  def __init__(self, lcd, touch_targets, latest_metrics, screen_dimensions):
    super().__init__(lcd, touch_targets, latest_metrics, screen_dimensions)

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
  def __init__(self, lcd, touch_targets, latest_metrics, screen_dimensions):
    super().__init__(lcd, touch_targets, latest_metrics, screen_dimensions)

  @staticmethod
  def get_core_icon_for_load(load):
    path = ''

    if load < 45:
      path = 'resources/core_low.png'
    elif load < 80:
      path = 'resources/core_medium.png'
    else:
      path = 'resources/core_high.png'

    return pygame.image.load(path)

  def render_detail_page(self):
    icon_img = pygame.image.load('resources/cpu_line_250.png')
    gpu_icon_rect = icon_img.get_rect(center=(50, self.screen_height - 50))
    SideshowPage.blit_alpha(self.lcd, icon_img, (gpu_icon_rect.x, gpu_icon_rect.y), .28)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['cpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(left=SideshowPage.MARGIN, bottom=self.screen_height)
    self.lcd.blit(text_surface, rect)

    core_label_text_surfaces = [ self.font_small.render('Core %s' % core, True, SideshowPage.OFF_WHITE) for (core, _) in enumerate(self.latest_metrics['load']['cpu'])]
    core_label_text_rects = [ core_label_text_surface.get_rect(left=self.screen_width - 120, top=int(core) * 25 + 20) for (core, core_label_text_surface) in enumerate(core_label_text_surfaces) ]

    load_text_surfaces = [ self.font_small.render('%d%%' % round(float(load['load'])), True, SideshowPage.OFF_WHITE) for (_, load) in enumerate(self.latest_metrics['load']['cpu'])]
    load_text_rects = [ load_text_surface.get_rect(right=self.screen_width - 20, top=int(core) * 25 + 20) for (core, load_text_surface) in enumerate(load_text_surfaces) ]

    core_icons = [ CpuDetailPage.get_core_icon_for_load(round(float(load['load']))) for (core, load) in enumerate(self.latest_metrics['load']['cpu'])]
    core_icon_rects = [ core_icon.get_rect(left=self.screen_width - 152, centery=load_text_rects[core].centery - 2) for (core, core_icon) in enumerate(core_icons) ]

    for i in range(len(load_text_surfaces)):
      self.lcd.blit(core_icons[i], core_icon_rects[i])
      self.lcd.blit(core_label_text_surfaces[i], core_label_text_rects[i])
      self.lcd.blit(load_text_surfaces[i], load_text_rects[i])


class GpuDetailPage(SideshowDetailPage):
  def __init__(self, lcd, touch_targets, latest_metrics, screen_dimensions):
    super().__init__(lcd, touch_targets, latest_metrics, screen_dimensions)

  def render_detail_page(self):
    icon_img = pygame.image.load('resources/gpu_line_250.png')
    gpu_icon_rect = icon_img.get_rect(center=(50, self.screen_height - 90))
    SideshowPage.blit_alpha(self.lcd, icon_img, (gpu_icon_rect.x, gpu_icon_rect.y), .28)

    text_surface = self.font_big.render('%s°' % self.latest_metrics['temps']['gpu'], True, SideshowPage.OFF_WHITE)
    rect = text_surface.get_rect(left=SideshowPage.MARGIN, bottom=self.screen_height)
    self.lcd.blit(text_surface, rect)
