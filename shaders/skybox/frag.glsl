#version 330 core

in vec2 clipboxPosition;

uniform samplerCube cubeMapTex;
uniform mat4 invViewProjectionMatrix;

out vec4 outColor;

void main() {
    vec4 direction_4d = invViewProjectionMatrix * vec4(clipboxPosition, 1, 1);
    vec3 direction_3d = normalize(direction_4d.xyz / direction_4d.w);

    // Flip the z-component of the direction vector (to match the professor's screenshots)
    direction_3d.z = -direction_3d.z;

    outColor = texture(cubeMapTex, direction_3d);
}
