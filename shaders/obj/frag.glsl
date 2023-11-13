#version 330 core

in vec3 fragNormal;
in vec3 frag_pos;
in vec2 fragUV;
// in vec4 gl_FragCoord;
// in vec2 screen_pos;

uniform vec3 eye_pos;
uniform sampler2D tex2D;
uniform samplerCube cubeMapTex;
uniform bool isGlowing;
uniform vec3 glowColor;
uniform float time;

out vec4 outColor;

void main() {
    // Compute normalized vectors and reflection vector.
    vec3 N = normalize(fragNormal);
    vec3 V = normalize(eye_pos - frag_pos);
    vec3 R = reflect(-V, N);
    
    // Sample color from 2D texture and cube map.
    vec3 color_tex = texture(tex2D, fragUV).rgb;
    vec3 envColor = texture(cubeMapTex, R).rgb;

    if (isGlowing) {
        // Parameters for Fresnel and pulsing effect
        float fresnelBias = 0.1;
        float fresnelScale = 1.0;
        float fresnelPower = 2.0;
        float frequency = 1.5;  // Lower frequency for slower pulsing
        float amplitude = 0.5;  // Higher amplitude for more pronounced glow
        float glowScale = 3.5;  // Scale to increase the emphasis on glowColor

        float glowIntensity = 0.5 + sin(time * frequency) * amplitude;
        float fresnel = fresnelBias + fresnelScale * pow(1.0 - dot(V, N), fresnelPower);
        vec3 fresnelGlow = glowColor * glowIntensity * fresnel * glowScale;

        vec3 finalColor = mix(color_tex, fresnelGlow, fresnel * glowIntensity);
        outColor = vec4(mix(finalColor, envColor, 0.2), 1.0);
    }
    else {
        // Regular rendering without glow
        outColor = vec4(mix(color_tex, envColor, 0.2), 1.0);
    }

}