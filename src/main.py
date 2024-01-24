from ursina import *
from FirstPersonController import Player, AABB


if __name__ == "__main__":
    app = Ursina(borderless=False)

    raymarch_shader = Shader.load(Shader.GLSL, vertex="./raymarcher.vert", fragment="./raymarcher.frag")

    cube = Entity(model="cube", scale=15, double_sided=True, shader=raymarch_shader)

    floor_collider = AABB(Vec3(0, -0.5, 0), Vec3(0, 0, 0), Vec3(15, 0, 15))
    wall_1_collider = AABB(Vec3(7.5, 1.5, 0), Vec3(0, 0, 0), Vec3(1, 3, 15))
    wall_2_collider = AABB(Vec3(-7.5, 1.5, 0), Vec3(0, 0, 0), Vec3(1, 3, 15))
    wall_3_collider = AABB(Vec3(0, 1.5, 7.5), Vec3(0, 0, 0), Vec3(15, 3, 1))
    wall_4_collider = AABB(Vec3(0, 1.5, -7.5), Vec3(0, 0, 0), Vec3(15, 3, 1))

    colliders = [floor_collider, wall_1_collider, wall_2_collider, wall_3_collider, wall_4_collider]

    player = Player(colliders=colliders, position=Vec3(0, 2, 0))


    def input(key):
        if key == "escape":
            mouse.locked = not mouse.locked

        if key == "n":
            player.noclip_mode = not player.noclip_mode

    app.run()