#version 330 core

layout (location = 0) in vec3 position;
layout (location = 1) in vec3 normal;
layout (location = 2) in vec2 uv;

uniform mat4 model_matrix;
uniform mat4 view_matrix;
uniform mat4 projection_matrix;


uniform mat4 light_projection_mat;
uniform mat4 light_view_mat;

out vec3 frag_pos;
out vec3 fragNormal;
out vec2 fragUV;
out vec4 fragPosLightSpace;
// out vec2 screen_pos;

void main() {
    // Transform the position from object space to world space using the model matrix
    vec4 world_pos = model_matrix * vec4(position, 1.0);
    frag_pos = world_pos.xyz;

    // Transform the position from world space to the clip coordinates
    
    gl_Position = projection_matrix * view_matrix * world_pos;
    fragPosLightSpace = light_projection_mat * light_view_mat * world_pos;
    // vec3 ndc = gl_Position.xyz / gl_Position.w;
    // screen_pos = ndc.xy * 0.5 + 0.5;

    // For normal attribute, transform the normal of the vertex by using the transpose of the inverse of the model matrix.
    mat4 normal_matrix = transpose(inverse(model_matrix));
    vec3 new_normal = (normal_matrix * vec4(normal, 0)).xyz;
    fragNormal = normalize(new_normal);

    fragUV = uv;
}