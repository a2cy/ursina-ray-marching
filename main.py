from ursina import *

from FirstPersonController import Player, AABBCollider


app = Ursina(borderless=False)

raymarch_shader = Shader.load(Shader.GLSL, vertex="./raymarcher.vert", fragment="./raymarcher.frag")

grass_texture = load_texture("grass")

Sky()

cube = Entity(model="cube", scale=16, double_sided=True, shader=raymarch_shader)

light = Entity(model="sphere", scale=.2, position=Vec3(0, 5, 0))

cube.set_shader_input("u_light_position", light.position)
cube.set_shader_input("u_texture", grass_texture)

floor_collider = AABBCollider(Vec3(0, -0.5, 0), Vec3(0), Vec3(15, 0, 15))
wall_1_collider = AABBCollider(Vec3(7.5, 1.5, 0), Vec3(0), Vec3(1, 3, 15))
wall_2_collider = AABBCollider(Vec3(-7.5, 1.5, 0), Vec3(0), Vec3(1, 3, 15))
wall_3_collider = AABBCollider(Vec3(0, 1.5, 7.5), Vec3(0), Vec3(15, 3, 1))
wall_4_collider = AABBCollider(Vec3(0, 1.5, -7.5), Vec3(0), Vec3(15, 3, 1))

colliders = [floor_collider, wall_1_collider, wall_2_collider, wall_3_collider, wall_4_collider]

player = Player(colliders=colliders, position=Vec3(0, 2, 0))


def input(key):
    if key == "escape":
        player.enabled = not player.enabled

    if key == "n":
        player.noclip_mode = not player.noclip_mode


app.run()