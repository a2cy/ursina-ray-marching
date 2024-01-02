from ursina import *


if __name__ == "__main__":
    app = Ursina(borderless=False)

    raymarch_shader = Shader.load(Shader.GLSL, vertex="./raymarcher.vert", fragment="./raymarcher.frag")

    cube = Entity(model="cube", scale=3, shader=raymarch_shader)

    EditorCamera()


    def update():
        cube.set_shader_input("u_resolution", window.size)

    app.run()