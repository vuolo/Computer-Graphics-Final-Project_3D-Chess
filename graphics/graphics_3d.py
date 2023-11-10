# Third-party imports.
from typing import Optional, Tuple
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
from constants import WINDOW, PIECES, PIECE_ABR_DICT, PIECE_COLORS, MODEL_TEMPLATE, CHESSBOARD_OBJECT_PATH, CHESSBOARD_TEXTURE_PATH, SKYBOX_PATH, PIECE_OBJECT_PATHS, PIECE_TEXTURE_PATHS, CAMERA_MOUSE_DRAG_SENSITIVITY, CAMERA_DEFAULT_YAW, CAMERA_DEFAULT_PITCH, CAMERA_MIN_DISTANCE, CAMERA_MAX_DISTANCE
from util.objLoaderV4 import ObjLoader
from util.cubemap import load_cubemap_textures, load_texture
from util.shaderLoaderV3 import ShaderProgram

# Global variables.
game: Optional['ChessGame'] = None
chessboard: dict = MODEL_TEMPLATE.copy()
pieces: dict = { color: { piece: MODEL_TEMPLATE.copy() for piece in PIECES } for color in PIECE_COLORS }
skybox: dict = {}
shaderProgram: Optional[ShaderProgram] = None

# ~ Camera
view_matrix: Optional[np.ndarray] = None
projection_matrix: Optional[np.ndarray] = None
rotated_eye: Optional[np.ndarray] = None
eye: np.ndarray = np.array([0, 0, 2])  # Make the camera "eye" 2 units away from the origin along the positive z-axis.
target: np.ndarray = np.array([0, 0, 0])  # Make the camera look at (target) the origin.
up: np.ndarray = np.array([0, 1, 0]) # Make the camera's "up" direction the positive y-axis.
near_plane: float = 0.1
far_plane: float = 10
fov: float = 75
# (Mouse dragging - rotate around the board - uses yaw/pitch instead of angleX/angleY):
is_dragging: bool = False
last_mouse_pos: Tuple[int, int] = (0, 0)
yaw: float = np.deg2rad(CAMERA_DEFAULT_YAW["white"])
pitch: float = np.deg2rad(CAMERA_DEFAULT_PITCH)
# (Mouse scrolling - zoom in/out - uses 
camera_distance: float = np.linalg.norm(eye)

# ~ Main
def setup_3d_graphics(new_game):
    global game, shaderProgram
    game = new_game
    
    # Set up OpenGL context's major and minor version numbers.
    pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 3)
    
    # MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
    # (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
    if platform.system() != 'Windows':
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    
    screen = pygame.display.set_mode(WINDOW["display"], DOUBLEBUF | OPENGL)
    
    # Set the background color to a medium dark shade of cyan-blue: #4c6680
    glClearColor(0.3, 0.4, 0.5, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # Setup the 3D scene.
    setup_generic_shaderProgram()
    setup_chessboard()
    setup_pieces()
    setup_skybox()
    
    return screen

# ~ Graphics
def draw_graphics():
    # Prepare the 3D scene.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the 3D scene.
    update_graphics()
    draw_chessboard()
    draw_pieces()
    draw_skybox()
    
def update_graphics():
    global rotated_eye, camera_distance, yaw, pitch, view_matrix, projection_matrix

    # Calculate camera position using spherical coordinates.
    camera_x = camera_distance * np.sin(pitch) * np.cos(yaw)
    camera_y = camera_distance * np.cos(pitch)
    camera_z = camera_distance * np.sin(pitch) * np.sin(yaw)
    rotated_eye = np.array([camera_x, camera_y, camera_z])

    view_matrix = pyrr.matrix44.create_look_at(rotated_eye, target, up)
    
    # Create a 4x4 projection matrix (to define the perspective projection).
    projection_matrix = pyrr.matrix44.create_perspective_projection(fov, WINDOW["aspect_ratio"], near_plane, far_plane)
    
def cleanup_graphics():
    global chessboard, skybox 
    glDeleteVertexArrays(2, [chessboard["vao"], skybox["vao"]])
    glDeleteBuffers(2, [chessboard["vbo"], skybox["vbo"]])
    glDeleteProgram(shaderProgram.shader)
    glDeleteProgram(skybox["shaderProgram"].shader)

# ~ Shader setup
def setup_generic_shaderProgram():
    global shaderProgram
    
    # Create a new (generic) shader program (compiles the object's shaders).
    shaderProgram = ShaderProgram("shaders/obj/vert.glsl", "shaders/obj/frag.glsl")
    
    # Assign the texture units to the shader.
    shaderProgram["tex2D"] = 0
    shaderProgram["cubeMapTex"] = 1

# ~ Chessboard
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
    
    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / chessboard["obj"].dia
    translation_matrix = pyrr.matrix44.create_from_translation(-chessboard["obj"].center)
    scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
    chessboard["model_matrix"] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
    
    # Load the object's texture.
    chessboard["texture"] = {}
    chessboard["texture"]["texture_pixels"], chessboard["texture"]["texture_size"] = load_texture(CHESSBOARD_TEXTURE_PATH, flip=True)
    chessboard["texture"]["texture_id"] = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, chessboard["texture"]["texture_id"])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, chessboard["texture"]["texture_size"]["width"], chessboard["texture"]["texture_size"]["height"],
                 0, GL_RGB, GL_UNSIGNED_BYTE, chessboard["texture"]["texture_pixels"])

def draw_chessboard():
    global chessboard, view_matrix, projection_matrix, rotated_eye, shaderProgram
    
    # Send each matrix (model, view, and projection) to the object's shader.
    glUseProgram(shaderProgram.shader)
    shaderProgram["model_matrix"] = chessboard["model_matrix"]
    shaderProgram["view_matrix"] = view_matrix
    shaderProgram["projection_matrix"] = projection_matrix
    shaderProgram["eye_pos"] = rotated_eye
    
    # Bind the object's texture.
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, chessboard["texture"]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

    # Draw the object.
    glBindVertexArray(chessboard["vao"])
    glDrawArrays(GL_TRIANGLES, 0, chessboard["obj"].n_vertices)

# ~ Pieces
def setup_pieces():
    global pieces
    for color in PIECE_COLORS:
        for piece in PIECES:
            # Load the 3D model for the piece (if the model has already been loaded for one color, it reuses that model for the other color to optimize resource usage).
            pieces[color][piece]["obj"] = pieces['black' if color == 'white' else 'white'][piece].get("obj") or ObjLoader(PIECE_OBJECT_PATHS[piece])
            
            # Create a VAO and VBO for the piece.
            pieces[color][piece]["vao"] = glGenVertexArrays(1)
            pieces[color][piece]["vbo"] = glGenBuffers(1)
            
            # Upload the piece's model data to the GPU.
            glBindVertexArray(pieces[color][piece]["vao"])
            glBindBuffer(GL_ARRAY_BUFFER, pieces[color][piece]["vbo"])
            glBufferData(GL_ARRAY_BUFFER, pieces[color][piece]["obj"].vertices, GL_STATIC_DRAW)
            
            # Configure the vertex attributes for the piece (position, normal, and uv).
            position_loc, normal_loc, uv_loc = 0, 1, 2
            glVertexAttribPointer(position_loc, pieces[color][piece]["obj"].size_position, GL_FLOAT, GL_FALSE, pieces[color][piece]["obj"].stride, ctypes.c_void_p(pieces[color][piece]["obj"].offset_position))
            glVertexAttribPointer(normal_loc, pieces[color][piece]["obj"].size_normal, GL_FLOAT, GL_FALSE, pieces[color][piece]["obj"].stride, ctypes.c_void_p(pieces[color][piece]["obj"].offset_normal))
            glVertexAttribPointer(uv_loc, pieces[color][piece]["obj"].size_texture, GL_FLOAT, GL_FALSE, pieces[color][piece]["obj"].stride, ctypes.c_void_p(pieces[color][piece]["obj"].offset_texture))
            glEnableVertexAttribArray(position_loc)
            glEnableVertexAttribArray(normal_loc)
            glEnableVertexAttribArray(uv_loc)
            
            # Create a 4x4 model matrix (to transform the piece from model space to world space).
            scale_factor = 2 / pieces[color][piece]["obj"].dia * 0.1075 # Scale the piece down to fit on the chessboard squares properly.
            translation_matrix = pyrr.matrix44.create_from_translation(-pieces[color][piece]["obj"].center)
            scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
            pieces[color][piece]["model_matrix"] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
            
            # Load the piece's texture.
            pieces[color][piece]["texture"] = {}
            pieces[color][piece]["texture"]["texture_pixels"], pieces[color][piece]["texture"]["texture_size"] = load_texture(PIECE_TEXTURE_PATHS[color][piece], flip=True)
            pieces[color][piece]["texture"]["texture_id"] = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, pieces[color][piece]["texture"]["texture_id"])
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, pieces[color][piece]["texture"]["texture_size"]["width"], pieces[color][piece]["texture"]["texture_size"]["height"],
                         0, GL_RGB, GL_UNSIGNED_BYTE, pieces[color][piece]["texture"]["texture_pixels"])
            
def draw_pieces():
    # `board_array` is a 8x8 grid (2d array) of chess pieces.
    #  • Each element in the grid is either None (if there is no piece at that location) or a <Piece> object.
    #   - The <Piece> object has a `value` attribute:
    #     • WHITE_PAWN = "P"
    #     • BLACK_PAWN = "p"
    #     • WHITE_KNIGHT = "N"
    #     • BLACK_KNIGHT = "n"
    #     • WHITE_BISHOP = "B"
    #     • BLACK_BISHOP = "b"
    #     • WHITE_ROOK = "R"
    #     • BLACK_ROOK = "r"
    #     • WHITE_QUEEN = "Q"
    #     • BLACK_QUEEN = "q"
    #     • WHITE_KING = "K"
    #     • BLACK_KING = "k"
    
    global pieces, game, view_matrix, projection_matrix, rotated_eye, shaderProgram
    board_array = game.get_2d_board_array()

    # Activate the shader program.
    glUseProgram(shaderProgram.shader)
    
    # Iterate over the 8x8 chessboard grid.
    for row in range(8):
        for col in range(8):
            piece = board_array[row][col]
            if piece:
                piece_char = piece.value
                
                # Determine the color and type of the piece.
                color = 'white' if piece_char.isupper() else 'black'
                piece_type = PIECE_ABR_DICT[piece_char.lower()] # Get the full name of the piece (e.g. "pawn", "knight", etc.).

                # Get the corresponding 3D model and shader for the piece.
                piece_model = pieces[color][piece_type]

                # Calculate the piece's model matrix based on its position on the board.
                piece_position = np.array([col - 3.5, 0, row - 3.5])  # Center the piece on the square.
                translation_matrix = pyrr.matrix44.create_from_translation(piece_position)
                model_matrix = pyrr.matrix44.multiply(translation_matrix, piece_model["model_matrix"])

                # Send each matrix (model, view, and projection) to the piece's shader.
                shaderProgram["model_matrix"] = model_matrix
                shaderProgram["view_matrix"] = view_matrix
                shaderProgram["projection_matrix"] = projection_matrix
                shaderProgram["eye_pos"] = rotated_eye

                # Bind the piece's texture.
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, piece_model["texture"]["texture_id"])

                # Bind the skybox texture (for environment mapping).
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

                # Draw the piece.
                glBindVertexArray(piece_model["vao"])
                glDrawArrays(GL_TRIANGLES, 0, piece_model["obj"].n_vertices)

# ~ Skybox
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

    # Upload the skybox's VAO data to the GPU.
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
    
# ~ Mouse events
def handle_mouse_events(events):
    global is_dragging, last_mouse_pos, yaw, pitch, camera_distance

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # (Left click)
                is_dragging = True
                last_mouse_pos = pygame.mouse.get_pos()
            elif event.button == 4:  # (Scroll up)
                camera_distance = max(CAMERA_MIN_DISTANCE, camera_distance - 1.0)
            elif event.button == 5:  # (Scroll down)
                camera_distance = min(CAMERA_MAX_DISTANCE, camera_distance + 1.0)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # (Left click - released)
                is_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if is_dragging:
                current_mouse_pos = pygame.mouse.get_pos()
                dx = current_mouse_pos[0] - last_mouse_pos[0]
                dy = current_mouse_pos[1] - last_mouse_pos[1]
                last_mouse_pos = current_mouse_pos

                # Update yaw and pitch based on mouse movement.
                yaw += np.deg2rad(dx * CAMERA_MOUSE_DRAG_SENSITIVITY)
                pitch -= np.deg2rad(dy * CAMERA_MOUSE_DRAG_SENSITIVITY)

                # Clamp pitch to prevent flipping.
                pitch = max(min(pitch, np.deg2rad(89)), np.deg2rad(-89))

# # ~ TODO: Mouse raycasting (for click detection)
# def get_ray_from_mouse(mouse_x, mouse_y):
#     # Convert mouse position to normalized device coordinates (NDC)
#     ndc_x = (2.0 * mouse_x) / WINDOW["width"] - 1.0
#     ndc_y = 1.0 - (2.0 * mouse_y) / WINDOW["height"]
#     ndc = np.array([ndc_x, ndc_y, -1.0, 1.0])  # Set z to -1 for the near plane and w to 1

#     # Transform NDC to homogeneous clip coordinates
#     clip = np.array([ndc_x, ndc_y, -1.0, 1.0])

#     # Transform clip coordinates to eye coordinates
#     eye = np.linalg.inv(projection_matrix) @ clip
#     eye = np.array([eye[0], eye[1], -1.0, 0.0])  # Set z to -1 and w to 0 for direction

#     # Transform eye coordinates to world coordinates
#     world = np.linalg.inv(view_matrix) @ eye
#     world /= np.linalg.norm(world)

#     # Ray origin is the camera position (eye)
#     ray_origin = eye[:3]

#     # Ray direction is the normalized world coordinates
#     ray_direction = world[:3]

#     return ray_origin, ray_direction

# def intersect_ray_with_plane(ray_origin, ray_direction, plane_origin, plane_normal):
#     # Calculate intersection using ray-plane intersection formula
#     denom = np.dot(ray_direction, plane_normal)
#     if np.abs(denom) > 1e-6:
#         p0l0 = plane_origin - ray_origin
#         t = np.dot(p0l0, plane_normal) / denom
#         if t >= 0:  # Check if the intersection is in the direction of the ray
#             intersection = ray_origin + t * ray_direction
#             # Logging to help debug
#             print(f"Intersection T: {t}, Intersection Point: {intersection}")
#             return intersection
#     return None

# def determine_square_from_intersection(intersection_point):
#     # Assuming the chessboard is 8x8 units and centered at the origin
#     chessboard_size = 0.75
#     half_chessboard_size = chessboard_size / 2

#     # Convert the intersection point to a local position relative to the chessboard center
#     local_pos_x = (intersection_point[0] + half_chessboard_size) / chessboard_size * 8
#     local_pos_z = (intersection_point[2] + half_chessboard_size) / chessboard_size * 8

#     # Normalize the local position to the range [0, 7]
#     file_index = int(local_pos_x)
#     rank_index = int(local_pos_z)

#     # Ensure the indices are within the bounds [0, 7]
#     file_index = min(max(file_index, 0), 7)
#     rank_index = min(max(rank_index, 0), 7)

#     # Convert the indices to chess notation
#     file_letter = chr(ord('a') + file_index)
#     rank_number = str(8 - rank_index)

#     # Logging to help debug
#     print(f"Local X: {local_pos_x}, Local Z: {local_pos_z}")
#     print(f"File Index: {file_index}, Rank Index: {rank_index}")
#     print(f"File Letter: {file_letter}, Rank Number: {rank_number}")
    
#     return file_letter + rank_number