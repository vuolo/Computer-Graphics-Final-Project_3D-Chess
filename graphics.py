# Third-party imports.
from typing import Optional
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame
import pyrr
import numpy as np
import chess
import platform

# Local application imports.
import chess_game
from constants import WINDOW, SKYBOX_PATH
# from graphics_2d import display_turn_indicator
from util.objLoaderV4 import ObjLoader
from util.cubemap import load_cubemap_textures
from util.shaderLoaderV3 import ShaderProgram

# Define the camera parameters.
eye = (0, 0, 2)  # 2 units away from the origin along the positive z-axis.
target = (0, 0, 0)  # The camera is looking at the origin.
up = (0, 1, 0)
near_plane = 0.1
far_plane = 10

# Global variables.
game: Optional['chess_game.ChessGame'] = None

def graphics_setup(new_game):
    global game
    game = new_game
    
    # Set up OpenGL context's major and minor version numbers.
    pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.set_mode(WINDOW["display"], DOUBLEBUF | OPENGL)
    
    # MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
    # (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
    if platform.system() == 'Linux':
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    
    # Set the background color to a medium dark shade of cyan-blue: #4c6680
    glClearColor(0.3, 0.4, 0.5, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # TODO: More lighting setup can be added here.
    setup_skybox()
    

def graphics_draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the board and pieces.
    draw_3d_chessboard()
    draw_3d_pieces(game)
            
    draw_skybox()

def graphics_cleanup():
    # TODO: cleanup
    # glDeleteVertexArrays(NUM_OBJECTS + 1, np.append(vaos, skybox["vao"]))
    # glDeleteBuffers(NUM_OBJECTS + 1, np.append(vbos, skybox["vbo"]))
    # for shaderProgram in shaderPrograms:
    #     glDeleteProgram(shaderProgram.shader)
    # glDeleteProgram(skybox["shaderProgram"].shader)
    pass

def setup_skybox():
    # Load the skybox shader and texture.
    global skybox
    skybox = {
        "shaderProgram": ShaderProgram("shaders/skybox/vert.glsl", "shaders/skybox/frag.glsl"),
        "texture_id": load_cubemap_textures([f"{SKYBOX_PATH}/right.png", f"{SKYBOX_PATH}/left.png",
                                    f"{SKYBOX_PATH}/top.png", f"{SKYBOX_PATH}/bottom.png",
                                    f"{SKYBOX_PATH}/front.png", f"{SKYBOX_PATH}/back.png"]),
        "vertices": np.array([-1, -1,
                            1, -1,
                            1, 1,
                            1, 1,
                            -1, 1,
                            -1, -1], dtype=np.float32),
        "size_position": 2,
        "offset_position": 0,
        "vao": glGenVertexArrays(1),
        "vbo": glGenBuffers(1),
        "position_loc": 0,
    }
    skybox["stride"] = skybox["size_position"] * 4
    skybox["n_vertices"] = len(skybox["vertices"]) // 2

    glBindVertexArray(skybox["vao"])
    glBindBuffer(GL_ARRAY_BUFFER, skybox["vbo"])
    glBufferData(GL_ARRAY_BUFFER, skybox["vertices"], GL_STATIC_DRAW)

    # Configure the vertex attributes for the skybox (position only).
    glUseProgram(skybox["shaderProgram"].shader)
    glBindAttribLocation(skybox["shaderProgram"].shader,
                        skybox["position_loc"], "position")
    glVertexAttribPointer(skybox["position_loc"], skybox["size_position"], GL_FLOAT,
                        GL_FALSE, skybox["stride"], ctypes.c_void_p(skybox["offset_position"]))
    glEnableVertexAttribArray(skybox["position_loc"])
    skybox["shaderProgram"]["cubeMapTex"] = 0
    
def draw_3d_chessboard():
    pass
    # for x in range(8):
    #     for y in range(8):
    #         glPushMatrix()
    #         if (x + y) % 2 == 0:
    #             glColor3f(1, 1, 1)  # White squares
    #         else:
    #             glColor3f(0, 0, 0)  # Black squares
    #         glTranslatef(x, 0, y)
    #         glutSolidCube(1)  # Draw a 1x1x1 cube here
    #         glPopMatrix()

def draw_3d_pieces(game):
    board_array = game.get_2d_board_array()
    # This function will now need to draw 3D models instead of text
    # TODO: Load your 3D piece models and draw them on the board.
    pass  # TODO: Replace this with your model loading and rendering code

def get_ray_from_mouse(mouse_x, mouse_y):
    # This is a complex function that would get the ray from the mouse
    # position into the 3D world.
    pass  # Replace this with your raycasting code

def select_piece(ray):
    # Determine if the ray intersects with any chess pieces.
    pass  # Replace this with your intersection code

def draw_skybox():
    # Grab the values from the GUI.
    angleY = np.deg2rad(0)
    angleX = np.deg2rad(0)
    fov = 45

    # Create a 4x4 view matrix (to transform the scene from world space to camera (view) space).
    # • Rotate the camera position using the rotation matrix (we combine the rotation matrices around the X and Y axes to create a single rotation matrix).
    rotationY_matrix = pyrr.matrix44.create_from_y_rotation(angleY)
    rotationX_matrix = pyrr.matrix44.create_from_x_rotation(angleX)
    rotation_matrix = pyrr.matrix44.multiply(
        rotationY_matrix, rotationX_matrix)
    rotated_eye = pyrr.matrix44.apply_to_vector(
        rotation_matrix, eye)
    view_matrix = pyrr.matrix44.create_look_at(rotated_eye, target, up)
    
    # Create a 4x4 projection matrix (to define the perspective projection).
    projection_matrix = pyrr.matrix44.create_perspective_projection(
        fov, WINDOW["aspect_ratio"], near_plane, far_plane)
    
    # Remove the translation component from the view matrix because we want the skybox to be static.
    view_matrix_without_translation = view_matrix.copy()
    view_matrix_without_translation[3][:3] = [0, 0, 0]
    inverseViewProjection_matrix = pyrr.matrix44.inverse(
        pyrr.matrix44.multiply(view_matrix_without_translation, projection_matrix))
    
    # Draw the skybox.
    glDepthFunc(GL_LEQUAL)
    glUseProgram(skybox["shaderProgram"].shader)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])
    skybox["shaderProgram"]["invViewProjectionMatrix"] = inverseViewProjection_matrix
    glBindVertexArray(skybox["vao"])
    glDrawArrays(GL_TRIANGLES, 0, skybox["n_vertices"])
    glDepthFunc(GL_LESS)