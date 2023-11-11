# Third-party imports.
import math
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
from util.animation import ease_in_out, add_shake, build_intro_camera_animations
from constants import WINDOW, PIECES, PIECE_ABR_DICT, PIECE_COLORS, MODEL_TEMPLATE, CHESSBOARD_OBJECT_PATH, CHESSBOARD_TEXTURE_PATH, SQUARE_OBJECT_PATH, HIGHLIGHTED_SQUARE_TEXTURE_PATH, SELECTED_SQUARE_TEXTURE_PATH, VALID_MOVES_SQUARE_TEXTURE_PATH, INVALID_MOVE_SQUARE_TEXTURE_PATH, SKYBOX_PATH, PIECE_OBJECT_PATHS, PIECE_TEXTURE_PATHS, CAMERA_MOUSE_DRAG_SENSITIVITY, CAMERA_DEFAULT_YAW, CAMERA_DEFAULT_PITCH, CAMERA_MIN_DISTANCE, CAMERA_MAX_DISTANCE, CAMERA_DEFAULT_ANIMATION_SPEED, CAMERA_USE_INTRO_ANIMATION, MOUSE_POSITION_DELTA, CAMERA_ZOOM_SCROLL_SENSITIVITY
from util.cubemap import load_cubemap_textures, load_texture
from util.game import notation_to_coords
from util.objLoaderV4 import ObjLoader
from util.shaderLoaderV3 import ShaderProgram

# Global variables.
game: Optional['ChessGame'] = None
chessboard: dict = MODEL_TEMPLATE.copy()
highlighted_square_model: dict = MODEL_TEMPLATE.copy()
selected_square_model: dict = MODEL_TEMPLATE.copy()
valid_move_square_model: dict = MODEL_TEMPLATE.copy()
invalid_move_square_model: dict = MODEL_TEMPLATE.copy()
pieces: dict = { color: { piece: MODEL_TEMPLATE.copy() for piece in PIECES } for color in PIECE_COLORS }
skybox: dict = {}
shaderProgram: Optional[ShaderProgram] = None

# ~ Camera
view_matrix: Optional[np.ndarray] = None
projection_matrix: Optional[np.ndarray] = None
rotated_eye: Optional[np.ndarray] = None
eye = np.array([0, 0, 2])  # Make the camera "eye" 2 units away from the origin along the positive z-axis.
target = np.array([0, 0, 0])  # Make the camera look at (target) the origin.
up = np.array([0, 1, 0]) # Make the camera's "up" direction the positive y-axis.
near_plane = 0.1
far_plane = 15
fov = 45
# (Mouse dragging - rotate around the board - uses yaw/pitch instead of angleX/angleY):
is_dragging = False
last_mouse_pos: Tuple[int, int] = (0, 0)
first_mouse_pos: Tuple[int, int] = (0, 0)
yaw: float = np.deg2rad(CAMERA_DEFAULT_YAW["white"])
pitch: float = np.deg2rad(CAMERA_DEFAULT_PITCH)
# (Mouse scrolling - zoom in/out - uses camera_distance to adjust the distance of the camera from the target):
camera_distance: float = np.linalg.norm(eye)
# (Camera-pan animation):
target_yaw = yaw
target_pitch = pitch
is_animating = False
animation_speed = CAMERA_DEFAULT_ANIMATION_SPEED
# (Intro camera animation):
intro_animation_started = CAMERA_USE_INTRO_ANIMATION
intro_animation_time = 0
intro_keyframes = build_intro_camera_animations(yaw, pitch, camera_distance)["20"] # Change from range 1 to 23 for varying intro camera animations
current_intro_keyframe = 0
# (Piece animation):
piece_animations = {}

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
    
    # Enable alpha blending (for transparency).
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Setup the 3D scene.
    setup_generic_shaderProgram()
    setup_chessboard()
    setup_pieces()
    setup_skybox()
    setup_highlights()
    
    return screen

# ~ Graphics
def draw_graphics(delta_time, highlighted_square, selected_square, valid_move_squares, invalid_move_square):
    global intro_animation_started
    if not intro_animation_started: update_camera_animation(delta_time)
    
    # Prepare the 3D scene.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the 3D scene.
    update_graphics(delta_time)
    draw_chessboard()
    draw_highlights(highlighted_square, selected_square, valid_move_squares, invalid_move_square)
    draw_pieces()
    draw_skybox()
    
def draw_highlights(highlighted_square, selected_square, valid_move_squares, invalid_move_square):
    global highlighted_square_model, selected_square_model, valid_move_square_model
    if highlighted_square != selected_square and highlighted_square != invalid_move_square: draw_at_board_position(highlighted_square_model, 7 - highlighted_square[1], highlighted_square[0])
    if selected_square: draw_at_board_position(selected_square_model, 7 - selected_square[1], selected_square[0])
    if valid_move_squares:
        for square in valid_move_squares:
            draw_at_board_position(valid_move_square_model, 7 - square[1], square[0])
    if invalid_move_square: draw_at_board_position(invalid_move_square_model, 7 - invalid_move_square[1], invalid_move_square[0])

def update_graphics(delta_time):
    global rotated_eye, camera_distance, yaw, pitch, view_matrix, projection_matrix, is_animating
    update_animations(delta_time)
    
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
    
# ~ Animations
def update_animations(delta_time):
    update_camera_animation(delta_time)
    for initial_piece_location, animation in piece_animations.items():
        if animation["is_active"]:
            update_piece_animation(animation, delta_time)
    
# ~ Camera intro animation
def start_intro_camera_animation():
    global intro_animation_time, current_intro_keyframe
    intro_animation_time = 0
    current_intro_keyframe = 0
    
def stop_intro_camera_animation():
    global intro_animation_started, current_intro_keyframe, yaw, pitch
    intro_animation_started = False
    current_intro_keyframe = len(intro_keyframes) - 1  # Set to the last keyframe.

# ~ Piece animation
def create_piece_animation(from_square, to_square, piece, start_time, duration):
    global piece_animations
    
    # Use the starting square as the unique key for the animation
    from_world_position = calculate_world_position(from_square)
    to_world_position = calculate_world_position(to_square)
    
    piece_animations[to_square] = {
        "start_position": from_world_position,
        "end_position": to_world_position,
        "current_position": from_world_position,
        "start_time": start_time,
        "duration": duration,
        "piece": piece,
        "from_square": from_square,
        "to_square": to_square,
        "is_active": True
    }

def update_piece_animation(animation, delta_time):
    current_time = pygame.time.get_ticks() / 1000.0
    progress = (current_time - animation["start_time"]) / animation["duration"]

    if progress < 1:
        # Define the proportions and maximum height as before
        ascend_proportion = 0.25
        descend_proportion = 0.25
        move_proportion = 0.5
        max_height = 2.5
        max_shake_intensity = 0.05

        # Adjust the range for shake progress
        if progress < ascend_proportion:  # Ascending phase
            eased_progress = ease_in_out(progress / ascend_proportion)
            height = eased_progress * max_height
            position = np.array([animation["start_position"][0], height, animation["start_position"][2]])

            # Apply shake towards the end of the ascending phase
            if progress > ascend_proportion * 0.7:  # Start shaking earlier
                shake_progress = (progress - ascend_proportion * 0.7) / (ascend_proportion * 0.3)
                position = add_shake(position, shake_progress, max_shake_intensity)

            animation["current_position"] = position
        
        elif progress < ascend_proportion + move_proportion:  # Moving phase
            eased_progress = ease_in_out((progress - ascend_proportion) / move_proportion)
            horizontal_position = interpolate(animation["start_position"], animation["end_position"], eased_progress)
            animation["current_position"] = np.array([horizontal_position[0], max_height, horizontal_position[2]])

        else:  # Descending phase
            eased_progress = ease_in_out((progress - ascend_proportion - move_proportion) / descend_proportion)
            height = max_height * (1 - eased_progress)
            position = np.array([animation["end_position"][0], height, animation["end_position"][2]])

            # Apply shake at the start of the descending phase
            if progress < ascend_proportion + move_proportion + descend_proportion * 0.3:  # Shake for a longer duration
                shake_progress = (progress - ascend_proportion - move_proportion) / (descend_proportion * 0.3)
                position = add_shake(position, shake_progress, max_shake_intensity)

            animation["current_position"] = position
    else:
        animation["is_active"] = False
        animation["current_position"] = animation["end_position"]

def interpolate(start_position, end_position, progress):
    # Use easing function to interpolate
    eased_progress = ease_in_out(progress)
    return tuple(np.add(start_position, np.multiply(np.subtract(end_position, start_position), eased_progress)))

def calculate_world_position(board_square):
    # Assuming the chessboard is 8x8 units and centered at the origin
    # and each square size is 1.575 units (as used in draw_piece_at_board_position).
    square_size = 1.575
    half_board_size = 8 / 2 * square_size

    # Convert algebraic chess notation to row and column
    file = ord(board_square[0]) - ord('a')
    rank = 8 - int(board_square[1])

    # Calculate the world position based on the row and column
    world_x = (file - 3.5) * square_size
    world_z = (rank - 3.5) * square_size
    world_y = 0  # Assuming the pieces are placed at y=0

    return np.array([world_x, world_y, world_z])

# ~ Camera rotation animation (ease-in-out)
def start_camera_rotation_animation(new_yaw_degrees=yaw, new_pitch_degrees=pitch):
    global target_yaw, target_pitch, is_animating
    target_yaw = np.deg2rad(new_yaw_degrees)
    target_pitch = np.deg2rad(new_pitch_degrees)
    is_animating = True
    
def update_camera_animation(delta_time):
    global yaw, pitch, camera_distance, intro_animation_time, current_intro_keyframe, intro_animation_started, is_animating, target_yaw, target_pitch
    
    # If the intro animation is active, update it.
    if intro_animation_started and current_intro_keyframe < len(intro_keyframes) - 1:
        # Calculate the progress between the current and the next keyframe.
        start_frame = intro_keyframes[current_intro_keyframe]
        end_frame = intro_keyframes[current_intro_keyframe + 1]
        frame_duration = end_frame["time"] - start_frame["time"]
        progress = (intro_animation_time - start_frame["time"]) / frame_duration
        eased_progress = ease_in_out(progress)
        
        # Interpolate yaw, pitch, and distance.
        yaw = np.interp(eased_progress, [0, 1], [start_frame["yaw"], end_frame["yaw"]])
        pitch = np.interp(eased_progress, [0, 1], [start_frame["pitch"], end_frame["pitch"]])
        camera_distance = np.interp(eased_progress, [0, 1], [start_frame["distance"], end_frame["distance"]])
        
        # Update the time and check if we should move to the next keyframe.
        intro_animation_time += delta_time
        if intro_animation_time >= end_frame["time"]:
            current_intro_keyframe += 1
            if current_intro_keyframe >= len(intro_keyframes) - 1:
                intro_animation_started = False  # End the intro animation.
    elif is_animating:
        # Define the threshold (in degrees) for when to stop the animation.
        threshold = 0.1

        # Convert yaw and pitch to degrees for easier control.
        yaw_degrees = np.rad2deg(yaw)
        pitch_degrees = np.rad2deg(pitch)
        target_yaw_degrees = np.rad2deg(target_yaw)
        target_pitch_degrees = np.rad2deg(target_pitch)

        # Calculate the difference between current and target angles in degrees.
        yaw_difference = target_yaw_degrees - yaw_degrees
        pitch_difference = target_pitch_degrees - pitch_degrees

        # Interpolate angles with an ease-out effect.
        yaw_degrees += yaw_difference * animation_speed * delta_time
        pitch_degrees += pitch_difference * animation_speed * delta_time

        # Convert back to radians for the view matrix calculation.
        yaw = np.deg2rad(yaw_degrees)
        pitch = np.deg2rad(pitch_degrees)

        # Check if the animation is close to finishing: if so, stop the animation.
        if abs(yaw_difference) < threshold and abs(pitch_difference) < threshold:
            yaw, pitch = np.deg2rad(target_yaw_degrees), np.deg2rad(target_pitch_degrees)
            is_animating = False

def rotate_camera_to_side(side):
    ''' Rotate the camera to view the board from a given side. '''
    global intro_animation_started
    # if intro_animation_started: stop_intro_camera_animation() # If the intro animation is in progress, stop it before starting a new one.
    
    # Wait 1 second before starting the camera animation (we wait for the `piece_animation` to finish).
    start_camera_rotation_animation(CAMERA_DEFAULT_YAW[side], CAMERA_DEFAULT_PITCH)

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

# ~ Highlights
def setup_highlights():
    global highlighted_square_model, selected_square_model, valid_move_square_model, invalid_move_square_model
    setup_highlight(highlighted_square_model, HIGHLIGHTED_SQUARE_TEXTURE_PATH)
    setup_highlight(selected_square_model, SELECTED_SQUARE_TEXTURE_PATH)
    setup_highlight(valid_move_square_model, VALID_MOVES_SQUARE_TEXTURE_PATH)
    setup_highlight(invalid_move_square_model, INVALID_MOVE_SQUARE_TEXTURE_PATH)

def setup_highlight(model, texture_path):
    model["obj"] = ObjLoader(SQUARE_OBJECT_PATH)
    
    # Create a VAO and VBO for the object.
    model["vao"] = glGenVertexArrays(1)
    model["vbo"] = glGenBuffers(1)
    
    # Upload the object's model data to the GPU.
    glBindVertexArray(model["vao"])
    glBindBuffer(GL_ARRAY_BUFFER, model["vbo"])
    glBufferData(GL_ARRAY_BUFFER, model["obj"].vertices, GL_STATIC_DRAW)
    
    # Configure the vertex attributes for the object (position, normal, and uv).
    position_loc, normal_loc, uv_loc = 0, 1, 2
    glVertexAttribPointer(position_loc, model["obj"].size_position, GL_FLOAT,
                          GL_FALSE, model["obj"].stride, ctypes.c_void_p(model["obj"].offset_position))
    glVertexAttribPointer(normal_loc, model["obj"].size_normal, GL_FLOAT,
                          GL_FALSE, model["obj"].stride, ctypes.c_void_p(model["obj"].offset_normal))
    glVertexAttribPointer(uv_loc, model["obj"].size_texture, GL_FLOAT,
                          GL_FALSE, model["obj"].stride, ctypes.c_void_p(model["obj"].offset_texture))
    glEnableVertexAttribArray(position_loc)
    glEnableVertexAttribArray(normal_loc)
    glEnableVertexAttribArray(uv_loc)
    
    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / model["obj"].dia * 0.1 # Scale the highlighted square down to fit on the chessboard squares properly.
    translation_matrix = pyrr.matrix44.create_from_translation(-model["obj"].center)
    scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
    model["model_matrix"] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
    
    # Load the object's texture.
    model["texture"] = {}
    model["texture"]["texture_pixels"], model["texture"]["texture_size"] = load_texture(texture_path, flip=True)
    model["texture"]["texture_id"] = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, model["texture"]["texture_id"])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, model["texture"]["texture_size"]["width"], model["texture"]["texture_size"]["height"],
                 0, GL_RGB, GL_UNSIGNED_BYTE, model["texture"]["texture_pixels"])

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
            scale_factor = 2 / pieces[color][piece]["obj"].dia * 0.1 # Scale the piece down to fit on the chessboard squares properly.
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
    global pieces, game, shaderProgram, piece_animations
    board_array = game.get_2d_board_array()

    # Activate the shader program.
    glUseProgram(shaderProgram.shader)
    
    # Iterate over the 8x8 chessboard grid, starting from the bottom-right corner (a1).
    for row in range(7, -1, -1):  # 7 corresponds to '1' in chess notation, and 0 corresponds to '8'
        for col in range(8):  # 0 corresponds to 'a' in chess notation, and 7 corresponds to 'h'
            piece = board_array[row][col]
            if piece:
                # Determine the color and type of the piece.
                color = 'white' if piece.value.isupper() else 'black'
                piece_type = PIECE_ABR_DICT[piece.value.lower()]
                piece_model = pieces[color][piece_type]
                piece_model['color'] = color

                # Determine the square name (e.g., 'e2')
                square_name = chr(col + ord('a')) + str(8 - row)

                # Check if there's an active animation for the piece on this square.
                if square_name in piece_animations and piece_animations[square_name]["is_active"]:
                    animation = piece_animations[square_name]
                    draw_piece_at_position(piece_model, animation["current_position"])
                else:
                    draw_at_board_position(piece_model, row, col)

def draw_piece_at_position(piece_model, position):
    global view_matrix, projection_matrix, rotated_eye, shaderProgram

    # Calculate the model matrix for the piece using the position.
    translation_matrix = pyrr.matrix44.create_from_translation(position)
    model_matrix = pyrr.matrix44.multiply(translation_matrix, piece_model["model_matrix"])
    
    # Apply additional rotation to the white pieces to face the center of the board.
    if piece_model['color'] == 'white':
        rotation_matrix = pyrr.matrix44.create_from_y_rotation(np.radians(180))
        model_matrix = pyrr.matrix44.multiply(rotation_matrix, model_matrix)

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

def draw_at_board_position(model, row, col):
    global view_matrix, projection_matrix, rotated_eye, shaderProgram

    # Calculate the piece's model matrix based on its position on the board.
    offset_x, offset_z, square_size = 0, 0, 1.575
    position = np.array([
        (col - 3.5) * square_size + offset_x, 
        0, 
        (row - 3.5) * square_size + offset_z
    ])
    translation_matrix = pyrr.matrix44.create_from_translation(position)
    model_matrix = pyrr.matrix44.multiply(translation_matrix, model["model_matrix"])
    
    # Apply additional rotation to the white pieces to face the center of the board.
    if 'color' in model and model['color'] == 'white':
        rotation_matrix = pyrr.matrix44.create_from_y_rotation(np.radians(180))
        model_matrix = pyrr.matrix44.multiply(rotation_matrix, model_matrix)

    # Send each matrix (model, view, and projection) to the piece's shader.
    shaderProgram["model_matrix"] = model_matrix
    shaderProgram["view_matrix"] = view_matrix
    shaderProgram["projection_matrix"] = projection_matrix
    shaderProgram["eye_pos"] = rotated_eye

    # Bind the piece's texture.
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, model["texture"]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

    # Draw the piece.
    glBindVertexArray(model["vao"])
    glDrawArrays(GL_TRIANGLES, 0, model["obj"].n_vertices)

# ~ Selected piece


# ~ Valid moves

           
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
def handle_mouse_events(events, on_click_callback):
    global is_dragging, last_mouse_pos, first_mouse_pos, yaw, pitch, camera_distance

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # (Left click)
                is_dragging = True
                last_mouse_pos = pygame.mouse.get_pos()
                first_mouse_pos = last_mouse_pos
            elif event.button == 4:  # (Scroll up)
                camera_distance = max(CAMERA_MIN_DISTANCE, camera_distance - CAMERA_ZOOM_SCROLL_SENSITIVITY)
            elif event.button == 5:  # (Scroll down)
                camera_distance = min(CAMERA_MAX_DISTANCE, camera_distance + CAMERA_ZOOM_SCROLL_SENSITIVITY)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # (Left click - released)
                current_mouse_pos = pygame.mouse.get_pos()
                delta_x = current_mouse_pos[0] - first_mouse_pos[0]
                delta_y = current_mouse_pos[1] - first_mouse_pos[1]
                delta_maginitude = math.sqrt(delta_x**2 + delta_y**2)
                if delta_maginitude < MOUSE_POSITION_DELTA:
                    x, y = current_mouse_pos
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

# def handle_ray_tracing(x, y):
#     ray_origin, ray_direction = get_ray_from_mouse(x, y)
#     print(f"Ray: {ray_origin, ray_direction}")
#     intersect_ray_with_object(ray_origin, ray_direction)
#     # intersect = intersect_ray_with_plane(ray_origin, ray_direction, np.array([0,0,0]), up)
#     # #print(f"Intersect: {intersect}")

#     # if intersect is not None:
#     #     # Step 4: Determine the chessboard square from the intersection
#     #     chess_square = determine_square_from_intersection(intersect)
#     #     print(f"Chess Square: {chess_square}")
#     #     return chess_square
#     # else:
#     #     print("No intersection with the chessboard.")
#     #     return None

# # # ~ TODO: Mouse raycasting (for click detection)
# def get_ray_from_mouse(mouse_x, mouse_y):
#     global view_matrix
#     # Convert mouse position to normalized device coordinates (NDC)
#     ndc_x = (2.0 * mouse_x) / WINDOW["width"] - 1.0
#     ndc_y = 1.0 - (2.0 * mouse_y) / WINDOW["height"]
#     ndc = np.array([ndc_x, ndc_y, 1.0, 1.0])  # Using 1.0 for z and w

#     # Transform NDC to eye coordinates
#     eye_coords = np.linalg.inv(projection_matrix) @ ndc
#     eye_coords = np.array([eye_coords[0], eye_coords[1], -1.0, 0.0])  # Direction vector

#     # Transform eye coordinates to world coordinates
#     world_coords = np.linalg.inv(view_matrix) @ eye_coords
#     world_coords /= np.linalg.norm(world_coords[0:3])  # Normalize the direction vector

#     # Ray origin (camera position in world space) and direction
#     ray_origin = np.linalg.inv(view_matrix) @ np.array([0, 0, 0, 1])  # Camera's position in world space
#     ray_direction = world_coords[0:3]

#     return ray_origin[0:3], ray_direction

# def intersect_ray_with_object(ray_origin, ray_direction):
#     global chessboard
#     # Transform the ray to the object's local space
#     inv_model_matrix = np.linalg.inv(chessboard["model_matrix"])
#     local_ray_origin = inv_model_matrix @ np.append(ray_origin, 1)
#     local_ray_direction = inv_model_matrix @ np.append(ray_direction, 0)

#     # Perform intersection test (e.g., with an AABB representing the object)
#     # This will vary depending on the shape of your objects
#     # Return True if intersecting, False otherwise
#     return is_intersecting(local_ray_origin[0:3], local_ray_direction[0:3], chessboard["bounds"])

# def is_intersecting(ray_origin, ray_direction, bounds):
#     print(f"bounds: {bounds}")
#     # # Unpack the bounds
#     # min_bound, max_bound = bounds

#     # # Initialize t_min and t_max
#     # t_min = (min_bound[0] - ray_origin[0]) / ray_direction[0]
#     # t_max = (max_bound[0] - ray_origin[0]) / ray_direction[0]

#     # if t_min > t_max:
#     #     t_min, t_max = t_max, t_min

#     # for i in range(1, 3):
#     #     t1 = (min_bound[i] - ray_origin[i]) / ray_direction[i]
#     #     t2 = (max_bound[i] - ray_origin[i]) / ray_direction[i]

#     #     if t1 > t2:
#     #         t1, t2 = t2, t1

#     #     if (t_min > t2) or (t1 > t_max):
#     #         return False

#     #     t_min = max(t_min, t1)
#     #     t_max = min(t_max, t2)

#     # return t_min < t_max and t_max > 0


# def intersect_ray_with_plane(ray_origin, ray_direction, plane_origin, plane_normal):
#     global chessboard
#     # Transform the plane origin and normal according to the chessboard's model_matrix
#     plane_origin = np.array([0, 0, 0, 1])
#     plane_normal = np.array([0, 1, 0, 0])  # Normal vector pointing upwards

#     transformed_plane_origin = chessboard["model_matrix"] @ plane_origin
#     transformed_plane_normal = chessboard["model_matrix"] @ plane_normal

#     # Calculate intersection using ray-plane intersection formula
#     denom = np.dot(ray_direction, transformed_plane_normal[:3])
#     if np.abs(denom) > 1e-6:
#         p0l0 = transformed_plane_origin[:3] - ray_origin
#         t = np.dot(p0l0, transformed_plane_normal[:3]) / denom
#         if t >= 0:  # Check if the intersection is in the direction of the ray
#             intersection = ray_origin + t * ray_direction
#             return intersection
#     return None


# def determine_square_from_intersection(intersection_point):
#     global chessboard
#     # Transform the intersection point to the chessboard's local coordinates
#     local_intersection_point = np.linalg.inv(chessboard["model_matrix"]) @ np.append(intersection_point, 1)

#     # Assuming each square is 1 unit in size in the chessboard's local coordinate system
#     local_pos_x = local_intersection_point[0] + 4
#     local_pos_z = local_intersection_point[2] + 4

#     # Normalize the local position to the range [0, 7]
#     file_index = int(local_pos_x)
#     rank_index = int(local_pos_z)

#     # Ensure the indices are within the bounds [0, 7]
#     file_index = min(max(file_index, 0), 7)
#     rank_index = min(max(rank_index, 0), 7)

#     # Convert the indices to chess notation
#     file_letter = chr(ord('a') + file_index)
#     rank_number = str(8 - rank_index)

#     return file_letter + rank_number