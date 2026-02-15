"""
UI Widgets Module
"""
import pygame
from config.settings import color_config, game_config

class TextInput:
    """Text input field"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 font: pygame.font.Font, max_length: int = 15):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_length = max_length
        self.text = ""
        self.active = True
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event: pygame.event.Event):
        """Handle keyboard input. Returns the text when Enter is pressed, None otherwise."""
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return self.text
            elif len(self.text) < self.max_length:
                if event.unicode.isprintable():
                    self.text += event.unicode
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, color_config.UI_BG, self.rect)
        pygame.draw.rect(surface, color_config.CYAN if self.active else color_config.UI_BORDER, 
                        self.rect, 3)
        
        text_surface = self.font.render(self.text, True, color_config.WHITE)
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)
        
        if self.active and self.cursor_visible and len(self.text) < self.max_length:
            cursor_x = text_rect.right + 5
            cursor_y1 = self.rect.centery - 15
            cursor_y2 = self.rect.centery + 15
            pygame.draw.line(surface, color_config.WHITE, 
                           (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
