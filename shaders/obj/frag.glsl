#version 330 core

in vec3 fragNormal;
in vec3 frag_pos;
in vec2 fragUV;

uniform vec3 eye_pos;
uniform int textureType; // 0 for (Environment mapping), 1 for (2D texture), 2 for (Mix)
uniform sampler2D tex2D;
uniform samplerCube cubeMapTex;

out vec4 outColor;

void main() {
    // Compute normalized vectors and reflection vector.
    vec3 N = normalize(fragNormal), V = normalize(eye_pos - frag_pos), R = reflect(-V, N);
    
    // Sample color from 2D texture and cube map.
    vec3 color_tex = texture(tex2D, fragUV).rgb, envColor = texture(cubeMapTex, R).rgb;
    
    // Use textureType to decide which color to use.
    outColor = vec4(
        (textureType == 0 ? envColor :              // Environment mapping
         textureType == 1 ? color_tex :             // 2D texture
         mix(color_tex, envColor, 0.2)), 1.0);      // Mix
}