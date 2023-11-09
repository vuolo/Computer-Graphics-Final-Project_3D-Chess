# Third-party imports.
import math
import pygame_menu

# Local application imports.
from constants import MAIN_MENU_BACKGROUND_IMAGE, SETTINGS_MENU_BACKGROUND_IMAGE

menu_theme = pygame_menu.themes.THEME_SOLARIZED.copy() # Copy a theme to build off of.
theme_extension = {
    # Menu general
    'background_color': (239, 231, 211, math.floor(255 * (1 - 0.9))), # 90% transparent.
    
    # Menubar/Title
    'title_background_color': (239, 231, 211, math.floor(255 * (1 - 0.2))), # 20% transparent.
    'title_font': pygame_menu.font.FONT_8BIT,
    'title_font_color': (0, 0, 0),
    'title_font_size': 64,
    'title_offset': (150, -2), # Position the title to the center of the screen.
    
    # Generic widget themes
    'widget_font': pygame_menu.font.FONT_BEBAS,
    'widget_font_color': (250, 250, 250),
    'widget_font_shadow': True,
    'widget_font_shadow_offset': 4,
    'widget_font_shadow_position': pygame_menu.locals.POSITION_SOUTHWEST,
    'widget_font_size': 48,
}
main_menu_background_image = pygame_menu.BaseImage(MAIN_MENU_BACKGROUND_IMAGE)
settings_menu_background_image = pygame_menu.BaseImage(SETTINGS_MENU_BACKGROUND_IMAGE)
[setattr(menu_theme, attr, value) for attr, value in theme_extension.items()] # Apply the theme extension.

def draw_main_menu_background(surface, menu_type='main'):
    if menu_type == 'main':
        main_menu_background_image.draw(surface)
    elif menu_type == 'settings':
        settings_menu_background_image.draw(surface)
        
    # TODO: Draw a 3D rotating chessboard with a skybox instead.