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
import time

# Local application imports.
from graphics.graphics_2d import setup_2d_graphics
from game.chess_game import ChessGame
from graphics.animation import ease_in_out, add_shake, build_intro_camera_animations
from constants import WINDOW, PIECES, PIECE_ABR_DICT, PIECE_COLORS, MODEL_TEMPLATE, CHESSBOARD_OBJECT_PATH, CLASSIC_CHESSBOARD_TEXTURE_PATH, WOOD_CHESSBOARD_TEXTURE_PATH, RGB_CHESSBOARD_TEXTURE_PATH, SQUARE_OBJECT_PATH, HIGHLIGHTED_SQUARE_TEXTURE_PATH, SELECTED_SQUARE_TEXTURE_PATH, VALID_MOVES_SQUARE_TEXTURE_PATH, INVALID_MOVE_SQUARE_TEXTURE_PATH, SKYBOX_PATHS, PIECE_OBJECT_PATHS, CLASSIC_PIECE_TEXTURE_PATHS, WOOD_PIECE_TEXTURE_PATHS, METAL_PIECE_TEXTURE_PATHS, CAMERA_MOUSE_DRAG_SENSITIVITY, CAMERA_DEFAULT_YAW, CAMERA_DEFAULT_PITCH, CAMERA_MIN_DISTANCE, CAMERA_MAX_DISTANCE, CAMERA_DEFAULT_ANIMATION_SPEED, CAMERA_USE_INTRO_ANIMATION, MOUSE_POSITION_DELTA, CAMERA_ZOOM_SCROLL_SENSITIVITY, HUD_TEXT_MODEL_OBJECT_PATH, HUD_TEXT_EXAMPLE_TEXTURE_PATH, BLACK_TURN_GLOW_COLOR, WHITE_TURN_GLOW_COLOR, CHECK_TURN_GLOW_COLOR, DISPLAY_TURN
from util.cubemap import load_cubemap_textures, load_texture
from util.game import notation_to_coords
from util.objLoaderV4 import ObjLoader
from util.shaderLoaderV3 import ShaderProgram
from util.guiV3 import SimpleGUI
from util.gui_ext import prepare_gui, update_gui
from graphics.graphics_shadows import render_shadow_map, setup_shadows

pygame.mixer.init()

# Global variables.
game: Optional['ChessGame'] = None
gui: Optional['SimpleGUI'] = None
chessboard: dict = MODEL_TEMPLATE.copy()
highlighted_square_model: dict = MODEL_TEMPLATE.copy()
selected_square_model: dict = MODEL_TEMPLATE.copy()
valid_move_square_model: dict = MODEL_TEMPLATE.copy()
invalid_move_square_model: dict = MODEL_TEMPLATE.copy()
pieces: dict = { color: { piece: MODEL_TEMPLATE.copy() for piece in PIECES } for color in PIECE_COLORS }
skybox: dict = {}
shaderProgram: Optional[ShaderProgram] = None
invalid_move_sound = pygame.mixer.Sound('./sounds/invalid-move.mp3')
invalid_move_sound.set_volume(0.25)
check_move_sound = pygame.mixer.Sound('./sounds/move-check.mp3')
check_move_sound_played = False


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
# Shadows
lightPos = np.array([1, 1, 1])
shadowTex_id = None
shadowBuffer_id = None
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
# ~ Piece animation:
piece_animations = {}
# ~ Hud text
hudShaderProgram: Optional[ShaderProgram] = None
hud_text_model: dict = MODEL_TEMPLATE.copy()
# ~ Indicators
indicator_squares = {
    "whos_turn": MODEL_TEMPLATE.copy()  # Assuming MODEL_TEMPLATE is a dictionary or similar structure
}
indicator_square_ext = {
    "whos_turn": {
        "texture_path": "models/indicators/whos_turn.png",
        "position": {
            "white": {
                "row": 0,
                "col": -2
            },
            "black": {
                "row": 7,
                "col": -2
            }
        }
    }
}
for key, nested_values in indicator_square_ext.items():
    if key in indicator_squares:
        for nested_key, nested_value in nested_values.items():
            indicator_squares[key][nested_key] = nested_value

# ~ Main
def setup_3d_graphics(new_game, new_gui, is_resume=False):
    global game, gui, shaderProgram, intro_animation_started, shadowTex_id, shadowBuffer_id
    game = new_game
    gui = new_gui
    
    # Reset the intro animation (if enabled).
    if not is_resume:
        intro_animation_started = CAMERA_USE_INTRO_ANIMATION
        start_intro_camera_animation()
    
    # Set up OpenGL context's major and minor version numbers.
    pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 3)
    
    # MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
    # (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
    if platform.system() != 'Windows':
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    
    screen = pygame.display.set_mode(WINDOW["display"], DOUBLEBUF | OPENGL)
    prepare_gui(gui, game)
    
    # Set the background color to a medium dark shade of cyan-blue: #4c6680
    glClearColor(0.3, 0.4, 0.5, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # Enable alpha blending (for transparency).
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    print("Selection", game.piece_selection)
    
    # Setup the 3D scene.
    setup_generic_shaderProgram()
    shadowBuffer_id, shadowTex_id = setup_shadows()
    setup_chessboard()
    setup_pieces()
    setup_skybox(game)
    setup_highlights()
    setup_indicators()
    
    # Setup the HUD text.
    # setup_hudShaderProgram()
    # setup_hud_text()
    
    return screen

# ~ Graphics
def draw_graphics(delta_time, highlighted_square, selected_square, valid_move_squares, invalid_move_square):
    global game, gui, intro_animation_started, chessboard, pieces, piece_animations
    if not intro_animation_started: update_camera_animation(delta_time)
    
    # Prepare the 3D scene.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the 3D scene.
    update_graphics(delta_time)
    render_shadow_map(game, chessboard, pieces, piece_animations)
    draw_chessboard()
    draw_highlights(highlighted_square, selected_square, valid_move_squares, invalid_move_square)
    # draw_indicators(game)
    draw_pieces()
    draw_skybox()
    
    # Draw text on top of the 3D scene.
    # draw_text("Sample Text", WINDOW["width"] / 2, WINDOW["height"] / 2)
    # draw_hud_text()
    
    update_gui(gui, game)
    
def draw_highlights(highlighted_square, selected_square, valid_move_squares, invalid_move_square):
    global highlighted_square_model, selected_square_model, valid_move_square_model
    if highlighted_square != selected_square and highlighted_square != invalid_move_square: draw_at_board_position(highlighted_square_model, 7 - highlighted_square[1], highlighted_square[0])
    if selected_square: draw_at_board_position(selected_square_model, 7 - selected_square[1], selected_square[0])
    if valid_move_squares:
        for square in valid_move_squares:
            draw_at_board_position(valid_move_square_model, 7 - square[1], square[0])
    if invalid_move_square: 
        invalid_move_sound.play()
        draw_at_board_position(invalid_move_square_model, 7 - invalid_move_square[1], invalid_move_square[0])
    
def setup_indicators():
    global indicator_squares
    for square_model in indicator_squares.values():
        setup_highlight(square_model, square_model["texture_path"], scale_factor=0.1)
    
def draw_indicators(game):
    global indicator_squares
    
    # Who's turn indicator
    indicator_to_use = "whos_turn"
    whos_turn = game.get_whos_turn()
    draw_at_board_position(indicator_squares[indicator_to_use], 7 - indicator_squares[indicator_to_use]["position"][whos_turn]["row"], indicator_squares[indicator_to_use]["position"][whos_turn]["col"])

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

# ~ HUD text
# def draw_text(text, x, y, font_size=32, color=(255, 255, 255)):
#     font = pygame.font.SysFont('arial', 64)
#     textSurface = font.render(text, True, color).convert_alpha()
#     textData = pygame.image.tostring(textSurface, "RGBA", True)
#     glWindowPos2d(x, y)
#     glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)
    
def setup_hud_text():
    global hud_text_model
    hud_text_model["obj"] = ObjLoader(HUD_TEXT_MODEL_OBJECT_PATH)
    
    # Create a VAO and VBO for the object.
    hud_text_model["vao"] = glGenVertexArrays(1)
    hud_text_model["vbo"] = glGenBuffers(1)
    
    # Upload the object's model data to the GPU.
    glBindVertexArray(hud_text_model["vao"])
    glBindBuffer(GL_ARRAY_BUFFER, hud_text_model["vbo"])
    glBufferData(GL_ARRAY_BUFFER, hud_text_model["obj"].vertices, GL_STATIC_DRAW)
    
    # Configure the vertex attributes for the object (position, normal, and uv).
    position_loc, normal_loc, uv_loc = 0, 1, 2
    glVertexAttribPointer(position_loc, hud_text_model["obj"].size_position, GL_FLOAT,
                          GL_FALSE, hud_text_model["obj"].stride, ctypes.c_void_p(hud_text_model["obj"].offset_position))
    glVertexAttribPointer(normal_loc, hud_text_model["obj"].size_normal, GL_FLOAT,
                          GL_FALSE, hud_text_model["obj"].stride, ctypes.c_void_p(hud_text_model["obj"].offset_normal))
    glVertexAttribPointer(uv_loc, hud_text_model["obj"].size_texture, GL_FLOAT,
                          GL_FALSE, hud_text_model["obj"].stride, ctypes.c_void_p(hud_text_model["obj"].offset_texture))
    glEnableVertexAttribArray(position_loc)
    glEnableVertexAttribArray(normal_loc)
    glEnableVertexAttribArray(uv_loc)
    
    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / hud_text_model["obj"].dia
    translation_matrix = pyrr.matrix44.create_from_translation(-hud_text_model["obj"].center)
    scale_matrix = pyrr.matrix44.create_from_scale([scale_factor, scale_factor, scale_factor])
    hud_text_model["model_matrix"] = pyrr.matrix44.multiply(translation_matrix, scale_matrix)
    
    # Load the object's texture.
    hud_text_model["texture"] = {}
    hud_text_model["texture"]["texture_pixels"], hud_text_model["texture"]["texture_size"] = load_texture(HUD_TEXT_EXAMPLE_TEXTURE_PATH, flip=True)
    hud_text_model["texture"]["texture_id"] = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, hud_text_model["texture"]["texture_id"])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, hud_text_model["texture"]["texture_size"]["width"], hud_text_model["texture"]["texture_size"]["height"],
                 0, GL_RGB, GL_UNSIGNED_BYTE, hud_text_model["texture"]["texture_pixels"])

# # It's recommend to draw head-up display elements using orthographic projection.
# # • Source: https://stackoverflow.com/a/54086253
# def draw_hud_text():
#     # # Apply the projection matrix to the projection matrix stack and the model matrix to the model view matrix stack.
#     # # • See glMatrixMode (https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/glMatrixMode.xml):
#     # glMatrixMode(GL_PROJECTION)
#     # gluPerspective(45, (WINDOW['width'] / WINDOW['height']), 0.1, 100.0)

#     # glMatrixMode(GL_MODELVIEW)
#     # glTranslatef(0.0, 0.0, -5)
    
#     # # Since the cross hair always should be on top of the view, you have to disable the depth test.
#     # glDisable(GL_DEPTH_TEST)

#     # mX, mY = pygame.mouse.get_pos()
#     # Crosshair(mX, 600-mY, 20)

#     # glEnable(GL_DEPTH_TEST)
    
#     # # Likely you can change the depth function (glDepthFunc) to GL_ALWAYS and change the glDepthMask.
    
#     # # Use glLoadIdentity to lad the identity matrix and use glOrtho to set up an orthographic projection 1:1 to window coordinates;
#     # glLoadIdentity()
#     # glOrtho(0.0, WINDOW['width'], 0.0, WINDOW['height'], -1.0, 1.0)
    
#     # # Use glPushMatrix/glPopMatrix to store and restore the matrixes on the matrix stack:
#     pass
  
def create_orthographic_projection_matrix():
    left, right = 0, WINDOW["width"]
    bottom, top = 0, WINDOW["height"]
    near, far = -1, 1
    return pyrr.matrix44.create_orthogonal_projection_matrix(left, right, bottom, top, near, far)

def draw_hud_text():
    global hud_text_model, hudShaderProgram

    # Use the shader program for HUD
    glUseProgram(hudShaderProgram.shader)

    # Create Orthographic Projection Matrix
    ortho_projection = create_orthographic_projection_matrix()

    # Update shader uniforms
    hudShaderProgram["model_matrix"] = hud_text_model["model_matrix"]
    hudShaderProgram["projection_matrix"] = ortho_projection

    # Disable Depth Test
    glDisable(GL_DEPTH_TEST)

    # Bind texture
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, hud_text_model["texture"]["texture_id"])

    # Draw the HUD Text
    glBindVertexArray(hud_text_model["vao"])
    glDrawArrays(GL_TRIANGLES, 0, hud_text_model["obj"].n_vertices)

    # Re-enable Depth Test
    glEnable(GL_DEPTH_TEST)

    # Unbind shader program
    glUseProgram(0)
    
# def draw_hud_text():
#     global hud_text_model, view_matrix, projection_matrix, rotated_eye, shaderProgram
    
#     # Get the inverse of the view matrix to obtain the camera's orientation.
#     inv_view_matrix = np.linalg.inv(view_matrix)

#     # Calculate a position in front of the camera.
#     # This position is relative to the near plane.
#     hud_distance = near_plane + 0.1  # Slightly in front of the near plane to avoid clipping.
#     hud_position = np.array([0, 0, -hud_distance, 1])  # In the camera's local space.

#     # Transform the position to world space using the inverse view matrix.
#     hud_position_world = inv_view_matrix @ hud_position

#     # Calculate the scale for the HUD text.
#     hud_scale = 0.15  # Adjust this value as needed for a suitable size.
#     hud_scale_matrix = pyrr.matrix44.create_from_scale([hud_scale, hud_scale, hud_scale])

#     # Create a rotation matrix to rotate the HUD text by 90 degrees around the x-axis.
#     hud_rotation_matrix = pyrr.matrix44.create_from_x_rotation(np.radians(90))

#     # Create a translation matrix to position the HUD text in front of the camera.
#     hud_translation_matrix = pyrr.matrix44.create_from_translation(hud_position_world[:3])

#     # Combine the scale, rotation, and translation transformations.
#     hud_model_matrix = pyrr.matrix44.multiply(hud_scale_matrix, hud_rotation_matrix)
#     hud_model_matrix = pyrr.matrix44.multiply(hud_model_matrix, hud_translation_matrix)

#     # Send the model matrix to the shader.
#     shaderProgram["model_matrix"] = hud_model_matrix
#     shaderProgram["view_matrix"] = np.eye(4)  # Use an identity matrix for the view matrix.
#     shaderProgram["projection_matrix"] = projection_matrix
#     shaderProgram["eye_pos"] = rotated_eye

#     # Bind the object's texture.
#     glActiveTexture(GL_TEXTURE0)
#     glBindTexture(GL_TEXTURE_2D, hud_text_model["texture"]["texture_id"])

#     # Draw the object.
#     glBindVertexArray(hud_text_model["vao"])
#     glDrawArrays(GL_TRIANGLES, 0, hud_text_model["obj"].n_vertices)
    
# ~ Shader setup
def setup_generic_shaderProgram():
    global shaderProgram
    
    # Create a new (generic) shader program (compiles the object's shaders).
    shaderProgram = ShaderProgram("shaders/obj/vert.glsl", "shaders/obj/frag.glsl")
    
    # Assign the texture units to the shader.
    shaderProgram["tex2D"] = 0
    shaderProgram["cubeMapTex"] = 1
    shaderProgram["depthTex"] = 2

    
def setup_hudShaderProgram():
    global hudShaderProgram
    
    # Create a new HUD shader program (compiles the hud's shaders).
    hudShaderProgram = ShaderProgram("shaders/hud/vert.glsl", "shaders/hud/frag.glsl")
    
    # Assign the texture units to the shader.
    hudShaderProgram["tex2D"] = 0
    
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
    if(game.board_selection == 0):
        chessboard["texture"]["texture_pixels"], chessboard["texture"]["texture_size"] = load_texture(WOOD_CHESSBOARD_TEXTURE_PATH, flip=True)
    elif(game.board_selection == 1):
        chessboard["texture"]["texture_pixels"], chessboard["texture"]["texture_size"] = load_texture(CLASSIC_CHESSBOARD_TEXTURE_PATH, flip=True)
    elif(game.board_selection == 2):
        chessboard["texture"]["texture_pixels"], chessboard["texture"]["texture_size"] = load_texture(RGB_CHESSBOARD_TEXTURE_PATH, flip=True)

    
    
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

def setup_highlight(model, texture_path, scale_factor=0.1):
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
    scale_factor = 2 / model["obj"].dia * scale_factor # Scale the highlighted square down to fit on the chessboard squares properly.
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
            
            if(game.piece_selection == 0):
                pieces[color][piece]["texture"]["texture_pixels"], pieces[color][piece]["texture"]["texture_size"] = load_texture(CLASSIC_PIECE_TEXTURE_PATHS[color][piece], flip=True)
            elif(game.piece_selection == 1):
                pieces[color][piece]["texture"]["texture_pixels"], pieces[color][piece]["texture"]["texture_size"] = load_texture(WOOD_PIECE_TEXTURE_PATHS[color][piece], flip=True)
            elif(game.piece_selection == 2):
                pieces[color][piece]["texture"]["texture_pixels"], pieces[color][piece]["texture"]["texture_size"] = load_texture(METAL_PIECE_TEXTURE_PATHS[color][piece], flip=True)

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
    global pieces, game, shaderProgram, piece_animations, check_move_sound_played
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

                # Glowing effect for King to show turn/check
                if(piece_type == "king" and DISPLAY_TURN):
                    is_white_turn = game.board.turn == chess.WHITE
                    is_in_check = game.board.is_check()
                    if is_white_turn and color == 'white':
                        if is_in_check:
                            if not check_move_sound_played:
                                check_move_sound.play()
                                check_move_sound_played = True
                                print('White in check sound')
                        else:
                            check_move_sound_played = False

                        shaderProgram["glowColor"] = CHECK_TURN_GLOW_COLOR if is_in_check else WHITE_TURN_GLOW_COLOR
                        shaderProgram["isGlowing"] = True
                        shaderProgram["time"] = pygame.time.get_ticks() / 1000.0
                    elif not is_white_turn and color == 'black':
                        if is_in_check:
                            if not check_move_sound_played:
                                check_move_sound.play()
                                check_move_sound_played = True
                                print('Black in check sound')
                        else:
                            check_move_sound_played = False

                        shaderProgram["glowColor"] = CHECK_TURN_GLOW_COLOR if is_in_check else BLACK_TURN_GLOW_COLOR
                        shaderProgram["isGlowing"] = True
                        shaderProgram["time"] = pygame.time.get_ticks() / 1000.0

                # Determine the square name (e.g., 'e2')
                square_name = chr(col + ord('a')) + str(8 - row)

                # Check if there's an active animation for the piece on this square.
                if square_name in piece_animations and piece_animations[square_name]["is_active"]:
                    animation = piece_animations[square_name]
                    draw_piece_at_position(piece_model, animation["current_position"])
                else:
                    draw_at_board_position(piece_model, row, col)
                shaderProgram["isGlowing"] = False


def draw_piece_at_position(piece_model, position):
    global view_matrix, projection_matrix, rotated_eye, shaderProgram, shadowTex_id

    # Calculate the model matrix for the piece using the position.
    translation_matrix = pyrr.matrix44.create_from_translation(position)
    model_matrix = pyrr.matrix44.multiply(translation_matrix, piece_model["model_matrix"])
    
    light_rotY_mat = pyrr.matrix44.create_from_y_rotation(np.deg2rad(0))
    rotated_lightPos = pyrr.matrix44.apply_to_vector(light_rotY_mat, lightPos)
    light_view_mat = pyrr.matrix44.create_look_at(rotated_lightPos, target, up)
    light_projection_mat = pyrr.matrix44.create_perspective_projection_matrix(45, WINDOW["aspect_ratio"], near_plane, far_plane)
    
    # Apply additional rotation to the white pieces to face the center of the board.
    if piece_model['color'] == 'white':
        rotation_matrix = pyrr.matrix44.create_from_y_rotation(np.radians(180))
        model_matrix = pyrr.matrix44.multiply(rotation_matrix, model_matrix)

    # Send each matrix (model, view, and projection) to the piece's shader.
    shaderProgram["model_matrix"] = model_matrix
    shaderProgram["view_matrix"] = view_matrix
    shaderProgram["projection_matrix"] = projection_matrix
    shaderProgram["eye_pos"] = rotated_eye
    shaderProgram["lightPos"] = lightPos
    shaderProgram["light_projection_mat"] = light_projection_mat
    shaderProgram["light_view_mat"] = light_view_mat

    # Bind the piece's texture.
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, piece_model["texture"]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])
    
    # Bind the shadow texture
    glActiveTexture(GL_TEXTURE2)
    glBindTexture(GL_TEXTURE_2D, shadowTex_id)

    # Draw the piece.
    glBindVertexArray(piece_model["vao"])
    glDrawArrays(GL_TRIANGLES, 0, piece_model["obj"].n_vertices)

def draw_at_board_position(model, row, col):
    global view_matrix, projection_matrix, rotated_eye, shaderProgram, shadowTex_id

    # Calculate the piece's model matrix based on its position on the board.
    offset_x, offset_z, square_size = 0, 0, 1.575
    position = np.array([
        (col - 3.5) * square_size + offset_x, 
        0, 
        (row - 3.5) * square_size + offset_z
    ])
    translation_matrix = pyrr.matrix44.create_from_translation(position)
    model_matrix = pyrr.matrix44.multiply(translation_matrix, model["model_matrix"])

    light_rotY_mat = pyrr.matrix44.create_from_y_rotation(np.deg2rad(0))
    rotated_lightPos = pyrr.matrix44.apply_to_vector(light_rotY_mat, lightPos)

    light_view_mat = pyrr.matrix44.create_look_at(rotated_lightPos, target, up)
    light_projection_mat = pyrr.matrix44.create_perspective_projection_matrix(45, WINDOW["aspect_ratio"], near_plane, far_plane)
    
    # Apply additional rotation to the white pieces to face the center of the board.
    if 'color' in model and model['color'] == 'white':
        rotation_matrix = pyrr.matrix44.create_from_y_rotation(np.radians(180))
        model_matrix = pyrr.matrix44.multiply(rotation_matrix, model_matrix)

    # Send each matrix (model, view, and projection) to the piece's shader.
    shaderProgram["model_matrix"] = model_matrix
    shaderProgram["view_matrix"] = view_matrix
    shaderProgram["projection_matrix"] = projection_matrix
    shaderProgram["eye_pos"] = rotated_eye
    shaderProgram["lightPos"] = lightPos
    shaderProgram["light_projection_mat"] = light_projection_mat
    shaderProgram["light_view_mat"] = light_view_mat

    # Bind the piece's texture.
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, model["texture"]["texture_id"])

    # Bind the skybox texture (for environment mapping).
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

    # Bind the shadow texture
    glActiveTexture(GL_TEXTURE2)
    glBindTexture(GL_TEXTURE_2D, shadowTex_id)

    # Draw the piece.
    glBindVertexArray(model["vao"])
    glDrawArrays(GL_TRIANGLES, 0, model["obj"].n_vertices)
           
# ~ Skybox
def setup_skybox(game):
    # Load the skybox shader and texture.
    global skybox, skybox_path

    skybox_path = SKYBOX_PATHS[game.skybox_selection]
    
    skybox = {
        "shaderProgram": ShaderProgram("shaders/skybox/vert.glsl", "shaders/skybox/frag.glsl"),
        "texture_id": load_cubemap_textures([f"{skybox_path}/right.png", f"{skybox_path}/left.png",
                                    f"{skybox_path}/top.png", f"{skybox_path}/bottom.png",
                                    f"{skybox_path}/front.png", f"{skybox_path}/back.png"]),
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
                    pass # Handle click event here
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