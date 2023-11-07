# Third-party imports.
import numpy as np
import pygame as pg
from OpenGL.GL import *
import pyrr

# Local application imports.
from guiV3 import SimpleGUI
from objLoaderV4 import ObjLoader
from shaderLoaderV3 import ShaderProgram
from utils import load_texture, load_cubemap, auto_position_gui

# Define constants.
OBJECT_PATH = "lordvoldemort/lordvoldemort.obj"
OBJECT_TEXTURE_PATH = "lordvoldemort/lordvoldemort.png"
SKYBOX_PATH = "skybox/1"
NUM_OBJECTS = 1
TRANSLATION_DISTANCE = 1.25
WINDOW = {
    "width": 860,
    "height": 480,
}
WINDOW.update({"aspect_ratio": WINDOW["width"] / WINDOW["height"]})

# Load each object.
objects = [ObjLoader(f"objects/{OBJECT_PATH}") for _ in range(NUM_OBJECTS)]
object_textures = [{} for _ in range(NUM_OBJECTS)]

# Define the camera parameters.
eye = (0, 0, 2)  # 2 units away from the origin along the positive z-axis.
target = (0, 0, 0)  # The camera is looking at the origin.
up = (0, 1, 0)
near_plane = 0.1
far_plane = 10

# Initialize a Simple GUI (using Tkinter) with sliders to control the rotation angles around the X and Y axes and the field of view.
gui = SimpleGUI("Assignment 9")
sliderY = gui.add_slider("Camera Y Angle", -180, 180,
                         initial_value=-26, resolution=1)
sliderX = gui.add_slider("Camera X Angle", -90, 90,
                         initial_value=5, resolution=1)
sliderFOV = gui.add_slider("FOV", 25, 120, initial_value=47, resolution=1)
radioTextureType = gui.add_radio_buttons(
    "Texture Type", {"Environment Mapping": 0, "2D Texture": 1, "Mix": 2}, initial_option="2D Texture")

# Initialize pygame and set up OpenGL context's major and minor version numbers.
pg.init()
pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)

# MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
# (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
pg.display.gl_set_attribute(
    pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
pg.display.gl_set_attribute(
    pg.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

# Create a window for graphics using OpenGL
pg.display.set_mode(
    (WINDOW["width"], WINDOW["height"]), pg.OPENGL | pg.DOUBLEBUF)
auto_position_gui(gui, WINDOW)

# Enable depth testing.
glEnable(GL_DEPTH_TEST)

# Create a VAO and VBO for each object (we type cast to np.array, then flatten to allow for NUM_OBJECTS = 1 and NUM_OBJECTS ≥ 2)
vaos = np.array([glGenVertexArrays(NUM_OBJECTS)]).flatten()
vbos = np.array([glGenBuffers(NUM_OBJECTS)]).flatten()

# Create a list of shaderPrograms and model matrices for each object.
shaderPrograms, model_matrices = [], []
position_loc, normal_loc, uv_loc = 0, 1, 2

for i, obj in enumerate(objects):
    # Upload the object's model data to the GPU.
    glBindVertexArray(vaos[i])
    glBindBuffer(GL_ARRAY_BUFFER, vbos[i])
    glBufferData(GL_ARRAY_BUFFER, obj.vertices, GL_STATIC_DRAW)

    # Create a new shader program (compiles the object's shaders).
    shaderPrograms.append(ShaderProgram(
        "shaders/obj/vert.glsl", "shaders/obj/frag.glsl"))

    # Configure the vertex attributes for the object (position, normal, and uv).
    glVertexAttribPointer(position_loc, obj.size_position, GL_FLOAT,
                          GL_FALSE, obj.stride, ctypes.c_void_p(obj.offset_position))
    glVertexAttribPointer(normal_loc, obj.size_normal, GL_FLOAT,
                          GL_FALSE, obj.stride, ctypes.c_void_p(obj.offset_normal))
    glVertexAttribPointer(uv_loc, obj.size_texture, GL_FLOAT,
                          GL_FALSE, obj.stride, ctypes.c_void_p(obj.offset_texture))
    glEnableVertexAttribArray(position_loc)
    glEnableVertexAttribArray(normal_loc)
    glEnableVertexAttribArray(uv_loc)

    # Assign the texture units to the shader.
    shaderPrograms[i]["tex2D"] = 0
    shaderPrograms[i]["cubeMapTex"] = 1

    # Create a 4x4 model matrix (to transform the object from model space to world space) for the object.
    scale_factor = 2 / obj.dia
    translation_matrix = pyrr.matrix44.create_from_translation(
        -obj.center)
    scale_matrix = pyrr.matrix44.create_from_scale(
        [scale_factor, scale_factor, scale_factor])
    model_matrices.append(pyrr.matrix44.multiply(
        translation_matrix, scale_matrix))

    # Load the object's texture.
    object_textures[i]["texture_pixels"], object_textures[i]["texture_size"] = load_texture(
        f"objects/{OBJECT_TEXTURE_PATH}", flip=True)
    object_textures[i]["texture_id"] = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, object_textures[i]["texture_id"])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, object_textures[i]["texture_size"]["width"], object_textures[i]["texture_size"]["height"],
                 0, GL_RGB, GL_UNSIGNED_BYTE, object_textures[i]["texture_pixels"])

# Load the skybox shader and texture.
skybox = {
    "shaderProgram": ShaderProgram("shaders/skybox/vert.glsl", "shaders/skybox/frag.glsl"),
    "texture_id": load_cubemap([f"{SKYBOX_PATH}/right.png", f"{SKYBOX_PATH}/left.png",
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

# Do the final rendering (run a loop to keep the program running).
draw = True
while draw:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            draw = False

    # Grab the values from the GUI.
    angleY = np.deg2rad(sliderY.get_value())
    angleX = np.deg2rad(sliderX.get_value())
    fov = sliderFOV.get_value()
    texture_type = radioTextureType.get_value()

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

    # Set the background color to a medium dark shade of cyan-blue: #4c6680
    glClearColor(0.3, 0.4, 0.5, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    for i, obj in enumerate(objects):
        # Dynamic translation based on i and the number of objects.
        distance = ((NUM_OBJECTS - 1) / 2 - i) * -TRANSLATION_DISTANCE
        translation_matrix = pyrr.matrix44.create_from_translation(
            [distance, 0.0, 0.0])

        # Combine the original model matrix with the translation matrix
        final_model_matrix = pyrr.matrix44.multiply(
            model_matrices[i], translation_matrix)

        # Send each matrix (model, view, and projection) to the object's shader.
        glUseProgram(shaderPrograms[i].shader)
        shaderPrograms[i]["model_matrix"] = final_model_matrix
        shaderPrograms[i]["view_matrix"] = view_matrix
        shaderPrograms[i]["projection_matrix"] = projection_matrix
        shaderPrograms[i]["eye_pos"] = rotated_eye

        # Send the texture type to the shader.
        #  • 0: Environment mapping
        #  • 1: 2D texture
        #  • 2: Mix
        shaderPrograms[i]["textureType"] = int(texture_type)

        # Bind the object's texture.
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, object_textures[i]["texture_id"])

        # Bind the skybox texture.
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, skybox["texture_id"])

        # Draw the object.
        glBindVertexArray(vaos[i])
        glDrawArrays(GL_TRIANGLES, 0, obj.n_vertices)

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

    # Refresh the display to show what's been drawn.
    pg.display.flip()

# Cleanup.
glDeleteVertexArrays(NUM_OBJECTS + 1, np.append(vaos, skybox["vao"]))
glDeleteBuffers(NUM_OBJECTS + 1, np.append(vbos, skybox["vbo"]))
for shaderProgram in shaderPrograms:
    glDeleteProgram(shaderProgram.shader)
glDeleteProgram(skybox["shaderProgram"].shader)

# Close the graphics window and exit the program.
pg.quit()
quit()
