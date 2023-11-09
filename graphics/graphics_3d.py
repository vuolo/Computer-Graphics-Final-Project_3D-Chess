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
from constants import WINDOW, CHESSBOARD_OBJECT_PATH, CHESSBOARD_TEXTURE_PATH, SKYBOX_PATH, PIECE_OBJECT_PATHS, PIECE_TEXTURE_PATHS
from util.objLoaderV4 import ObjLoader
from util.cubemap import load_cubemap_textures, load_texture
from util.shaderLoaderV3 import ShaderProgram

# Global variables.
game: Optional['ChessGame'] = None
skybox: Optional[dict] = None

# ~ Chessboard
chessboard: Optional[dict] = {
    "obj": None,
    "texture": {},
    "vao": None,
    "vbo": None,
    "shaderProgram": None,
    "model_matrix": None,
}

# ~ Pieces
pieces: Optional[dict] = {
    "white": {
        "king": {
            "obj": None,
            "model_matrix": None,
            "texture": None,
        },
        "queen": None,
        "rook": None,
        "bishop": None,
        "knight": None,
        "pawn": None,
    },
    "black": {
        "king": None,
        "queen": None,
        "rook": None,
        "bishop": None,
        "knight": None,
        "pawn": None,
    },
}

# ~ Camera
view_matrix: Optional[np.ndarray] = None
projection_matrix: Optional[np.ndarray] = None
rotated_eye: Optional[np.ndarray] = None
eye: np.ndarray = np.array([0, 0, 2])  # Make the camera "eye" 2 units away from the origin along the positive z-axis.
target: np.ndarray = np.array([0, 0, 0])  # Make the camera look at (target) the origin.
up: np.ndarray = np.array([0, 1, 0])
near_plane: float = 0.1
far_plane: float = 10
angleY: float = np.deg2rad(0)
angleX: float = np.deg2rad(20)
fov: float = 65

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
    global chessboard
    chessboard["obj"] = ObjLoader(CHESSBOARD_OBJECT_PATH)
    
    # Create a VAO and VBO for the object.
    chessboard["vao"] = glGenVertexArrays(1)
    chessboard["vbo"] = glGenBuffers(1)
    
    # Upload the object's model data to the GPU.
    glBindVertexArray(chessboard["vao"])
    glBindBuffer(GL_ARRAY_BUFFER, chessboard["vbo"])
    glBufferData(GL_ARRAY_BUFFER, chessboard["obj"].vertices, GL_STATIC_DRAW)
    
    # Create a new shader program (compiles the object's shaders).
    chessboard["shaderProgram"] = ShaderProgram("shaders/obj/vert.glsl", "shaders/obj/frag.glsl")
    
    # Configure the vertex attributes for the object (position, normal, and uv).
    position_loc, normal_loc, uv_loc = 0, 1, 2
    glVertexAttribPointer(position_loc, chessboard["obj"].size_position, GL_FLOAT,
                          GL_FALSE, chessboard["obj"].stride, ctypes.c_void_p(chessboard["obj"].offset_position))
    glVertexAttribPointer(normal_loc, chessboard["obj"].size_normal, GL_FLOAT,
                          GL_FALSE, chessboard["obj"].stride, ctypes.c_void_p(chessboard["obj"].offset_normal))
    glVertexAttribPointer(uv_loc, chessboard["obj"].size_texture, GL_FLOAT,
                          GL_FALSE, chessboard["obj"].stride, ctypes.c_void_p(chessboard["obj"].offset_texture))
    glEnableVertexAttribArray(position_loc)
    glEnableVertexAttribArray(normal_loc)
    glEnableVertexAttribArray(uv_loc)
    
    # Assign the texture units to the shader.
    chessboard["shaderProgram"]["tex2D"] = 0
    chessboard["shaderProgram"]["cubeMapTex"] = 1
    
    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / chessboard["obj"].dia
    translation_matrix = pyrr.matrix44.create_from_translation(-chessboard["obj"].center)
    scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
    chessboard["model_matrix"] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
    
    # Load the object's texture.
    chessboard["texture"]["texture_pixels"], chessboard["texture"]["texture_size"] = load_texture(CHESSBOARD_TEXTURE_PATH, flip=True)
    chessboard["texture"]["texture_id"] = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, chessboard["texture"]["texture_id"])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, chessboard["texture"]["texture_size"]["width"], chessboard["texture"]["texture_size"]["height"],
                 0, GL_RGB, GL_UNSIGNED_BYTE, chessboard["texture"]["texture_pixels"])

def draw_graphics():    
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
    global chessboard, skybox 
    glDeleteVertexArrays(2, [chessboard["vao"], skybox["vao"]])
    glDeleteBuffers(2, [chessboard["vbo"], skybox["vbo"]])
    glDeleteProgram(chessboard["shaderProgram"].shader)
    glDeleteProgram(skybox["shaderProgram"].shader)

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
                               1,  1,
                               1,  1,
                              -1,  1,
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
    global chessboard, view_matrix, projection_matrix, rotated_eye
    
    # Send each matrix (model, view, and projection) to the object's shader.
    glUseProgram(chessboard["shaderProgram"].shader)
    chessboard["shaderProgram"]["model_matrix"] = chessboard["model_matrix"]
    chessboard["shaderProgram"]["view_matrix"] = view_matrix
    chessboard["shaderProgram"]["projection_matrix"] = projection_matrix
    chessboard["shaderProgram"]["eye_pos"] = rotated_eye
    
    # Bind the object's texture.
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, chessboard["texture"]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

    # Draw the object.
    glBindVertexArray(chessboard["vao"])
    glDrawArrays(GL_TRIANGLES, 0, chessboard["obj"].n_vertices)
    

def setup_pieces():
    global pieces_obj, pieces_vao, pieces_vbo, pieces_shaderProgram, pieces_model_matrix, pieces_texture

    # Initialize dictionaries to hold the piece objects and textures.
    pieces_obj = {}
    pieces_vao = {}
    pieces_vbo = {}
    pieces_shaderProgram = {}
    pieces_model_matrix = {}
    pieces_texture = {}

    for piece_type in PIECE_OBJECT_PATHS:
        # Load the piece model using ObjLoader.
        pieces_obj[piece_type] = ObjLoader(PIECE_OBJECT_PATHS[piece_type])
        
        # Create a VAO and VBO for the piece.
        pieces_vao[piece_type] = glGenVertexArrays(1)
        pieces_vbo[piece_type] = glGenBuffers(1)
        
        # Upload the piece's model data to the GPU.
        glBindVertexArray(pieces_vao[piece_type])
        glBindBuffer(GL_ARRAY_BUFFER, pieces_vbo[piece_type])
        glBufferData(GL_ARRAY_BUFFER, pieces_obj[piece_type].vertices, GL_STATIC_DRAW)
        
        # You can use the same shader program for all pieces if they share the same shaders.
        # Otherwise, create a new shader program for each piece type.
        # This example assumes all pieces use the same shaders.
        if not pieces_shaderProgram:
            pieces_shaderProgram[piece_type] = ShaderProgram("shaders/obj/vert.glsl", "shaders/obj/frag.glsl")
        
        # Configure the vertex attributes for the piece (position, normal, and uv).
        position_loc, normal_loc, uv_loc = 0, 1, 2
        glVertexAttribPointer(position_loc, pieces_obj[piece_type].size_position, GL_FLOAT,
                              GL_FALSE, pieces_obj[piece_type].stride, ctypes.c_void_p(pieces_obj[piece_type].offset_position))
        glVertexAttribPointer(normal_loc, pieces_obj[piece_type].size_normal, GL_FLOAT,
                              GL_FALSE, pieces_obj[piece_type].stride, ctypes.c_void_p(pieces_obj[piece_type].offset_normal))
        glVertexAttribPointer(uv_loc, pieces_obj[piece_type].size_texture, GL_FLOAT,
                              GL_FALSE, pieces_obj[piece_type].stride, ctypes.c_void_p(pieces_obj[piece_type].offset_texture))
        glEnableVertexAttribArray(position_loc)
        glEnableVertexAttribArray(normal_loc)
        glEnableVertexAttribArray(uv_loc)

        # Load the textures for white and black pieces.
        pieces_texture[piece_type] = {}
        for color in PIECE_TEXTURE_PATHS:
            texture_path = PIECE_TEXTURE_PATHS[color][piece_type]
            texture_pixels, texture_size = load_texture(texture_path, flip=True)
            texture_id = glGenTextures(1)

            pieces_texture[piece_type][color] = {
                "texture_pixels": texture_pixels,
                "texture_size": texture_size,
                "texture_id": texture_id
            }

            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, texture_size["width"], texture_size["height"],
                         0, GL_RGB, GL_UNSIGNED_BYTE, texture_pixels)

        # Assign the texture units to the shader.
        pieces_shaderProgram[piece_type]["tex2D"] = 0  # Assuming all pieces use texture unit 0 for their texture.

        # Create a 4x4 model matrix for the piece.
        # You can create different transformations for each piece type if needed.
        # This example scales all pieces based on the first piece's bounding diameter.
        scale_factor = 2 / pieces_obj[piece_type].dia
        translation_matrix = pyrr.matrix44.create_from_translation(-pieces_obj[piece_type].center)
        scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
        pieces_model_matrix[piece_type] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)


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