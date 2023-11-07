import pygame as pg
from OpenGL.GL import *


def load_texture(filename, texture_format="RGB", flip=False):
    texture = pg.image.load(filename)
    return pg.image.tobytes(texture, texture_format, flip), {
        "width": texture.get_width(),
        "height": texture.get_height()
    }


def load_cubemap(file_names):
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, texture_id)

    parameters = [
        (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE),
        (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE),
        (GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE),
        (GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST),
        (GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    ]

    for param, value in parameters:
        glTexParameteri(GL_TEXTURE_CUBE_MAP, param, value)

    faces = [GL_TEXTURE_CUBE_MAP_POSITIVE_X, GL_TEXTURE_CUBE_MAP_NEGATIVE_X,
             GL_TEXTURE_CUBE_MAP_POSITIVE_Y, GL_TEXTURE_CUBE_MAP_NEGATIVE_Y,
             GL_TEXTURE_CUBE_MAP_POSITIVE_Z, GL_TEXTURE_CUBE_MAP_NEGATIVE_Z]

    for face, file_name in zip(faces, file_names):
        texture_pixels, size = load_texture(
            file_name, texture_format="RGB", flip=False)
        glTexImage2D(face, 0, GL_RGB, size['width'], size['height'],
                     0, GL_RGB, GL_UNSIGNED_BYTE, texture_pixels)

    glGenerateMipmap(GL_TEXTURE_CUBE_MAP)
    glBindTexture(GL_TEXTURE_CUBE_MAP, 0)

    return texture_id


def auto_position_gui(gui, WINDOW):
    PADDING_RIGHT = 20  # px
    TITLE_BAR_HEIGHT = 28  # px
    x = (gui.root.winfo_screenwidth() -
         WINDOW["width"]) // 2 - gui.root.winfo_width() - PADDING_RIGHT
    y = (gui.root.winfo_screenheight() -
         WINDOW["height"]) // 2 - TITLE_BAR_HEIGHT
    gui.root.geometry(
        f"{gui.root.winfo_width()}x{gui.root.winfo_height()}+{x}+{y}")
