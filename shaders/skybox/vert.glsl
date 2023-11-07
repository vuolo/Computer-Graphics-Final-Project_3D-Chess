#version 330 core

layout (location = 0) in vec2 position;

out vec2 clipboxPosition;

void main() {
    clipboxPosition = position;
    gl_Position = vec4(position, 1.0, 1.0);
}