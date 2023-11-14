
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from typing import Optional
from util.shaderLoaderV3 import ShaderProgram
from game.chess_game import ChessGame
import pyrr
import numpy as np
from constants import WINDOW, PIECE_ABR_DICT

shadowShaderProgram: Optional[ShaderProgram] = None
shadowDepthTex = None
lightPos = [1, 1, 1]
shadow_buffer_id = None

def setup_shadows():
    setup_shadow_shaderProgram()
    return create_framebuffer_with_depth_attachment()

def create_framebuffer_with_depth_attachment():
    # Create a framebuffer object
    global shadow_buffer_id, shadowDepthTex
    shadow_buffer_id = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, shadow_buffer_id)

    # Create a texture object for the depth attachment
    shadowDepthTex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, shadowDepthTex)

    # Define texture parameters
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, WINDOW['width'], WINDOW['height'], 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)  # Set texture filtering parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Attach the depth texture to the framebuffer
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, shadowDepthTex, 0)

    # Tell OpenGL which color attachments we'll use (of this framebuffer) for rendering.
    # We won't be using any color attachments so we can tell OpenGL that we're not going to bind any color attachments.
    # So set the draw and read buffer to none
    glDrawBuffer(GL_NONE)
    glReadBuffer(GL_NONE)

    # Check if framebuffer is complete
    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        raise Exception("Framebuffer is not complete!")

    # Unbind the framebuffer
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    return shadow_buffer_id, shadowDepthTex

def render_shadow_map(game: ChessGame, chessboard: dict, pieces: dict, piece_animations: dict):
    glBindFramebuffer(GL_FRAMEBUFFER, shadow_buffer_id)
    glClear(GL_DEPTH_BUFFER_BIT)

    # ***** render the object and receiver *****
    glUseProgram(shadowShaderProgram.shader)

    # Draw each object that will cast shadows
    draw_objects(game, chessboard, pieces, piece_animations)

    glBindFramebuffer(GL_FRAMEBUFFER, 0)

def draw_objects(game: ChessGame, chessboard: dict, pieces: dict, piece_animations: dict):
    
    # glBindFramebuffer(GL_FRAMEBUFFER, shadow_buffer_id)
    board_array = game.get_2d_board_array()
    target = (0,0,0)
    up = (0,1,0)
    near = 0.1
    far = 15

    # view and projection matrices for light's point of view
    light_rotY_mat = pyrr.matrix44.create_from_y_rotation(np.deg2rad(0))
    rotated_lightPos = pyrr.matrix44.apply_to_vector(light_rotY_mat, lightPos)

    light_view_mat = pyrr.matrix44.create_look_at(rotated_lightPos, target, up)
    light_projection_mat = pyrr.matrix44.create_perspective_projection_matrix(45, WINDOW["aspect_ratio"], near, far)

    # Now draw our pieces
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
                    translation_matrix = pyrr.matrix44.create_from_translation(animation["current_position"])
                    model_matrix = pyrr.matrix44.multiply(translation_matrix, piece_model["model_matrix"])
                else: # Calculate the piece's model matrix based on its position on the board.
                    offset_x, offset_z, square_size = 0, 0, 1.575
                    position = np.array([
                        (col - 3.5) * square_size + offset_x, 
                        0, 
                        (row - 3.5) * square_size + offset_z
                    ])
                    translation_matrix = pyrr.matrix44.create_from_translation(position)
                    model_matrix = pyrr.matrix44.multiply(translation_matrix, piece_model["model_matrix"])
                    
                # Apply additional rotation to the white pieces to face the center of the board.
                if 'color' in piece_model and piece_model['color'] == 'white':
                    rotation_matrix = pyrr.matrix44.create_from_y_rotation(np.radians(180))
                    model_matrix = pyrr.matrix44.multiply(rotation_matrix, model_matrix)
                # Send each matrix (model, view, and projection) to the shadow shader.
                shadowShaderProgram["modelMatrix"] = model_matrix
                shadowShaderProgram["viewMatrix"] = light_view_mat
                shadowShaderProgram["projectionMatrix"] = light_projection_mat
                # Draw the piece.
                glBindVertexArray(piece_model["vao"])
                # glBindBuffer(GL_ARRAY_BUFFER, piece_model["vbo"])
                glDrawArrays(GL_TRIANGLES, 0, piece_model["obj"].n_vertices)
    # glBindFramebuffer(GL_FRAMEBUFFER, 0)
    
    # This is for the chessboard, but we don't actually need it since there is nothing for the
    # chessboard to cast shadows onto
    shadowShaderProgram["modelMatrix"] = chessboard["model_matrix"]
    shadowShaderProgram["viewMatrix"] = light_view_mat
    shadowShaderProgram["projectionMatrix"] = light_projection_mat
    glBindVertexArray(chessboard["vao"])
    glDrawArrays(GL_TRIANGLES, 0, chessboard["obj"].n_vertices)

                
def setup_shadow_shaderProgram():
    global shadowShaderProgram
    shadowShaderProgram = ShaderProgram("shaders/shadow/vert.glsl", "shaders/shadow/frag.glsl")