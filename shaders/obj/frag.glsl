#version 330 core

in vec3 fragNormal;
in vec3 frag_pos;
in vec2 fragUV;
// in vec4 gl_FragCoord;
// in vec2 screen_pos;

uniform vec3 eye_pos;
uniform sampler2D tex2D;
uniform samplerCube cubeMapTex;

out vec4 outColor;

void main() {
    // Compute normalized vectors and reflection vector.
    vec3 N = normalize(fragNormal);
    vec3 V = normalize(eye_pos - frag_pos);
    vec3 R = reflect(-V, N);
    
    // Sample color from 2D texture and cube map.
    vec3 color_tex = texture(tex2D, fragUV).rgb;
    vec3 envColor = texture(cubeMapTex, R).rgb;
    
    // Mix the two colors.
    outColor = vec4(mix(color_tex, envColor, 0.2), 1.0);
    // outColor = vec4(texture(tex2D, screen_pos).rgb, 1.0);
}