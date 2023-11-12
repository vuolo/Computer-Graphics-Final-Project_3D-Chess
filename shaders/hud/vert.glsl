#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec2 uv;

uniform mat4 model_matrix;
uniform mat4 projection_matrix; // Only model and projection matrices

out vec2 fragUV;

void main() {
    gl_Position = projection_matrix * model_matrix * vec4(position, 1.0);
    fragUV = uv;
}
