#version 330 core

in vec2 fragUV;
uniform sampler2D tex2D; // Texture for HUD elements

out vec4 outColor;

void main() {
    outColor = texture(tex2D, fragUV);
}
