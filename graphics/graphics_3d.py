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
from graphics.graphics_2d import setup_2d_graphics
from game.chess_game import ChessGame
from constants import WINDOW, CHESSBOARD_OBJECT_PATH, SKYBOX_PATH
from util.objLoaderV4 import ObjLoader
from util.cubemap import load_cubemap_textures
from util.shaderLoaderV3 import ShaderProgram

# Define the camera parameters.
eye = (0, 0, 2)  # 2 units away from the origin along the positive z-axis.
target = (0, 0, 0)  # The camera is looking at the origin.
up = (0, 1, 0)
near_plane = 0.1
far_plane = 10
angleY = np.deg2rad(0)
angleX = np.deg2rad(20)
fov = 65

# Global variables.
game: Optional['ChessGame'] = None
skybox: Optional[dict] = None
chessboard_obj: Optional['ObjLoader'] = None
chessboard_vao: Optional[int] = None
chessboard_vbo: Optional[int] = None
chessboard_shaderProgram: Optional['ShaderProgram'] = None
chessboard_model_matrix: Optional[np.ndarray] = None
view_matrix: Optional[np.ndarray] = None
projection_matrix: Optional[np.ndarray] = None
rotated_eye: Optional[np.ndarray] = None

def setup_3d_graphics(new_game):
    global game
    game = new_game
    
    # Set up OpenGL context's major and minor version numbers.
    pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 3)
    
    # MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
    # (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
    if platform.system() != 'Windows':
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    
    screen = pygame.display.set_mode(WINDOW["display"], DOUBLEBUF | OPENGL)
    
    # Set the background color to a medium dark shade of cyan-blue: #4c6680
    glClearColor(0.3, 0.4, 0.5, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    setup_chessboard()
    setup_skybox()
    
    return screen

def setup_chessboard():
    global chessboard_obj, chessboard_vao, chessboard_vbo, chessboard_shaderProgram, chessboard_model_matrix
    chessboard_obj = ObjLoader(CHESSBOARD_OBJECT_PATH)
    
    # Create a VAO and VBO for the object.
    chessboard_vao = glGenVertexArrays(1)
    chessboard_vbo = glGenBuffers(1)
    
    # Upload the object's model data to the GPU.
    glBindVertexArray(chessboard_vao)
    glBindBuffer(GL_ARRAY_BUFFER, chessboard_vbo)
    glBufferData(GL_ARRAY_BUFFER, chessboard_obj.vertices, GL_STATIC_DRAW)
    
    # Create a new shader program (compiles the object's shaders).
    chessboard_shaderProgram =ShaderProgram("shaders/obj/vert.glsl", "shaders/obj/frag.glsl")
    
    # Configure the vertex attributes for the object (position, normal, and uv).
    position_loc, normal_loc, uv_loc = 0, 1, 2
    glVertexAttribPointer(position_loc, chessboard_obj.size_position, GL_FLOAT,
                          GL_FALSE, chessboard_obj.stride, ctypes.c_void_p(chessboard_obj.offset_position))
    glVertexAttribPointer(normal_loc, chessboard_obj.size_normal, GL_FLOAT,
                          GL_FALSE, chessboard_obj.stride, ctypes.c_void_p(chessboard_obj.offset_normal))
    glVertexAttribPointer(uv_loc, chessboard_obj.size_texture, GL_FLOAT,
                          GL_FALSE, chessboard_obj.stride, ctypes.c_void_p(chessboard_obj.offset_texture))
    glEnableVertexAttribArray(position_loc)
    glEnableVertexAttribArray(normal_loc)
    glEnableVertexAttribArray(uv_loc)
    
    # Assign the texture units to the shader.
    chessboard_shaderProgram["tex2D"] = 0
    chessboard_shaderProgram["cubeMapTex"] = 1
    
    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / chessboard_obj.dia
    translation_matrix = pyrr.matrix44.create_from_translation(-chessboard_obj.center)
    scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
    chessboard_model_matrix = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
    
    # # TODO: Load the object's texture.
    # object_textures[i]["texture_pixels"], object_textures[i]["texture_size"] = load_texture(
    #     f"objects/{OBJECT_TEXTURE_PATH}", flip=True)
    # object_textures[i]["texture_id"] = glGenTextures(1)
    # glBindTexture(GL_TEXTURE_2D, object_textures[i]["texture_id"])
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    # glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, object_textures[i]["texture_size"]["width"], object_textures[i]["texture_size"]["height"],
    #              0, GL_RGB, GL_UNSIGNED_BYTE, object_textures[i]["texture_pixels"])

def draw_graphics():
    global game
    
    # Prepare the 3D scene.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the 3D scene.
    update_graphics()
    draw_3d_chessboard()
    draw_3d_pieces()
    draw_skybox()
    
def update_graphics():
    global angleX, angleY, eye, target, up, fov, near_plane, far_plane, view_matrix, projection_matrix, rotated_eye
    
    # Create a 4x4 view matrix (to transform the scene from world space to camera (view) space).
    # • Rotate the camera position using the rotation matrix (we combine the rotation matrices around the X and Y axes to create a single rotation matrix).
    rotationY_matrix = pyrr.matrix44.create_from_y_rotation(angleY)
    rotationX_matrix = pyrr.matrix44.create_from_x_rotation(angleX)
    rotation_matrix = pyrr.matrix44.multiply(rotationY_matrix, rotationX_matrix)
    rotated_eye = pyrr.matrix44.apply_to_vector(rotation_matrix, eye)
    view_matrix = pyrr.matrix44.create_look_at(rotated_eye, target, up)
    
    # Create a 4x4 projection matrix (to define the perspective projection).
    projection_matrix = pyrr.matrix44.create_perspective_projection(fov, WINDOW["aspect_ratio"], near_plane, far_plane)
    

def cleanup_graphics():
    global skybox
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
    glBindAttribLocation(skybox["shaderProgram"].shader, skybox["position_loc"], "position")
    glVertexAttribPointer(skybox["position_loc"], skybox["size_position"], GL_FLOAT, GL_FALSE, skybox["stride"], ctypes.c_void_p(skybox["offset_position"]))
    glEnableVertexAttribArray(skybox["position_loc"])
    skybox["shaderProgram"]["cubeMapTex"] = 0
    
    return skybox
    
def draw_3d_chessboard():
    global chessboard_obj, chessboard_vao, chessboard_shaderProgram, chessboard_model_matrix, view_matrix, projection_matrix, rotated_eye
    
    # Send each matrix (model, view, and projection) to the object's shader.
    glUseProgram(chessboard_shaderProgram.shader)
    chessboard_shaderProgram["model_matrix"] = chessboard_model_matrix
    chessboard_shaderProgram["view_matrix"] = view_matrix
    chessboard_shaderProgram["projection_matrix"] = projection_matrix
    chessboard_shaderProgram["eye_pos"] = rotated_eye
    
    # # Bind the object's texture.
    # glActiveTexture(GL_TEXTURE0)
    # glBindTexture(GL_TEXTURE_2D, object_textures[i]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    # glActiveTexture(GL_TEXTURE1)
    # glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

    # Draw the object.
    glBindVertexArray(chessboard_vao)
    glDrawArrays(GL_TRIANGLES, 0, chessboard_obj.n_vertices)
    

def draw_3d_pieces():
    global game
    board_array = game.get_2d_board_array()
    # This function will now need to draw 3D models instead of text.
    # TODO: Load our 3D piece models and draw them on the board.
    pass  # TODO: Replace this with our model loading and rendering code

def get_ray_from_mouse(mouse_x, mouse_y):
    # This is a complex function that would get the ray from the mouse
    # position into the 3D world.
    pass  # TODO: Replace this with our raycasting code

def select_piece(ray):
    # Determine if the ray intersects with any chess pieces.
    pass  # TODO: Replace this with our intersection code

def draw_skybox():
    global skybox, view_matrix, projection_matrix
    
    # Remove the translation component from the view matrix because we want the skybox to be static.
    view_matrix_without_translation = view_matrix.copy()
    view_matrix_without_translation[3][:3] = [0, 0, 0]
    inverseViewProjection_matrix = pyrr.matrix44.inverse(pyrr.matrix44.multiply(view_matrix_without_translation, projection_matrix))
    
    # Draw the skybox.
    glDepthFunc(GL_LEQUAL)
    glUseProgram(skybox["shaderProgram"].shader)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])
    skybox["shaderProgram"]["invViewProjectionMatrix"] = inverseViewProjection_matrix
    glBindVertexArray(skybox["vao"])
    glDrawArrays(GL_TRIANGLES, 0, skybox["n_vertices"])
    glDepthFunc(GL_LESS)