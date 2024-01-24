#version 150

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

in vec4 p3d_Vertex;

out vec3 fragcoord;


void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;

    fragcoord = vec3(p3d_ModelMatrix * p3d_Vertex);
}
