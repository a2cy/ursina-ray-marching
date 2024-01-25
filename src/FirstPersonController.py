from ursina import *


class AABB:
    def __init__(self, position, origin, scale):
        self.position = position
        self.origin = origin
        self.scale = scale


    @property
    def x(self):
        return self.position.x + self.origin.x

    @property
    def y(self):
        return self.position.y + self.origin.y

    @property
    def z(self):
        return self.position.z + self.origin.z

    @property
    def x_1(self):
        return self.position.x + self.origin.x - self.scale.x / 2

    @property
    def y_1(self):
        return self.position.y + self.origin.y - self.scale.y / 2

    @property
    def z_1(self):
        return self.position.z + self.origin.z - self.scale.z / 2

    @property
    def x_2(self):
        return self.position.x + self.origin.x + self.scale.x / 2

    @property
    def y_2(self):
        return self.position.y + self.origin.y + self.scale.y / 2

    @property
    def z_2(self):
        return self.position.z + self.origin.z + self.scale.z / 2


class Player(Entity):

    def __init__(self, colliders, **kwargs):
        super().__init__()

        self.walk_speed = 6
        self.fall_speed = 32
        self.gravity = 2
        self.acceleration = 16
        self.jump_height = 1

        self.noclip_speed = 8
        self.noclip_acceleration = 6
        self.noclip_mode = False

        self.colliders = colliders
        self.aabb_collider = AABB(self.position, Vec3(0, -.8, 0), Vec3(.8, 1.8, .8))

        self.camera_pivot = Entity(parent=self)
        camera.parent = self.camera_pivot
        camera.position = Vec3(0,0,0)
        camera.rotation = Vec3(0,0,0)
        camera.fov = 90
        self.mouse_sensitivity = 80

        self.grounded = False
        self.direction = Vec3(0,0,0)
        self.velocity = Vec3(0,0,0)

        for key, value in kwargs.items():
            setattr(self, key, value)


    def aabb_broadphase(self, collider_1, collider_2, direction):
        x_1 = min(collider_1.x_1, collider_1.x_1 + direction.x)
        y_1 = min(collider_1.y_1, collider_1.y_1 + direction.y)
        z_1 = min(collider_1.z_1, collider_1.z_1 + direction.z)

        x_2 = max(collider_1.x_2, collider_1.x_2 + direction.x)
        y_2 = max(collider_1.y_2, collider_1.y_2 + direction.y)
        z_2 = max(collider_1.z_2, collider_1.z_2 + direction.z)

        return (x_1 < collider_2.x_2 and x_2 > collider_2.x_1 and
                y_1 < collider_2.y_2 and y_2 > collider_2.y_1 and
                z_1 < collider_2.z_2 and z_2 > collider_2.z_1)


    def swept_aabb(self, collider_1, collider_2, direction):
        get_time = lambda x, y: x / y if y else float("-" * (x > 0) + "inf")

        x_entry = get_time(collider_2.x_1 - collider_1.x_2 if direction.x > 0 else collider_2.x_2 - collider_1.x_1, direction.x)
        x_exit = get_time(collider_2.x_2 - collider_1.x_1 if direction.x > 0 else collider_2.x_1 - collider_1.x_2, direction.x)

        y_entry = get_time(collider_2.y_1 - collider_1.y_2 if direction.y > 0 else collider_2.y_2 - collider_1.y_1, direction.y)
        y_exit = get_time(collider_2.y_2 - collider_1.y_1 if direction.y > 0 else collider_2.y_1 - collider_1.y_2, direction.y)

        z_entry = get_time(collider_2.z_1 - collider_1.z_2 if direction.z > 0 else collider_2.z_2 - collider_1.z_1, direction.z)
        z_exit = get_time(collider_2.z_2 - collider_1.z_1 if direction.z > 0 else collider_2.z_1 - collider_1.z_2, direction.z)

        if x_entry < 0 and y_entry < 0 and z_entry < 0:
            return 1, Vec3(0, 0, 0)

        if x_entry > 1 or y_entry > 1 or z_entry > 1:
            return 1, Vec3(0, 0, 0)

        entry_time = max(x_entry, y_entry, z_entry)
        exit_time = min(x_exit, y_exit, z_exit)

        if entry_time > exit_time:
            return 1, Vec3(0, 0, 0)

        normal_x = (0, -1 if direction.x > 0 else 1)[entry_time == x_entry]
        normal_y = (0, -1 if direction.y > 0 else 1)[entry_time == y_entry]
        normal_z = (0, -1 if direction.z > 0 else 1)[entry_time == z_entry]

        return entry_time, Vec3(normal_x, normal_y, normal_z)


    def update(self):
        if self.noclip_mode:
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity

            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

            self.direction = Vec3(self.camera_pivot.forward * (held_keys["w"] - held_keys["s"])
                                  + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            self.direction += self.up * (held_keys["e"] - held_keys["q"])

            self.velocity = lerp(self.velocity, self.direction * self.noclip_speed, self.noclip_acceleration * time.dt)

            self.position += self.velocity * time.dt

        else:
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity

            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

            if self.grounded and held_keys["space"]:
                self.velocity.y = 2 * (self.fall_speed * self.gravity * self.jump_height)**.5

            self.direction = Vec3(self.forward * (held_keys["w"] - held_keys["s"])
                                  + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            self.velocity.xz = lerp(self.velocity, self.direction * self.walk_speed, self.acceleration * time.dt).xz
            self.velocity.y = lerp(self.velocity.y, -self.fall_speed, self.gravity * time.dt)

            self.aabb_collider.position = self.position

            self.grounded = False

            for _ in range(3):
                velocity = self.velocity * time.dt
                collisions = []

                for collider in self.colliders:
                    if self.aabb_broadphase(self.aabb_collider, collider, velocity):
                        collision_time, collision_normal = self.swept_aabb(self.aabb_collider, collider, velocity)

                        collisions.append((collision_time, collision_normal))

                if not collisions:
                    break

                collision_time, collision_normal = min(collisions, key= lambda x: x[0])
                collision_time -= .0001

                if collision_normal.x:
                    self.velocity.x = 0
                    self.position.x += velocity.x * collision_time

                if collision_normal.y:
                    self.velocity.y = 0
                    self.position.y += velocity.y * collision_time

                if collision_normal.z:
                    self.velocity.z = 0
                    self.position.z += velocity.z * collision_time

                if collision_normal.y == 1:
                    self.grounded = True

            self.position += self.velocity * time.dt


    def on_enable(self):
        mouse.locked = True


    def on_disable(self):
        mouse.locked = False


if __name__ == "__main__":
    app = Ursina(borderless=False)

    ground = Entity(model="plane", texture="grass", scale=Vec3(1000, 1, 1000), texture_scale=Vec2(1000, 1000))
    ground_collider = AABB(Vec3(0, 0, 0), Vec3(0, 0, 0), Vec3(1000, 1, 1000))

    wall_1 = Entity(model="cube", texture="brick", collider="box", scale=Vec3(1, 3, 5), position=Vec3(5, 1.5, 0), texture_scale=Vec2(5, 3))
    wall_1_collider = AABB(Vec3(5, 1.5, 0), Vec3(0, 0, 0), Vec3(1, 3, 5))

    wall_2 = Entity(model="cube", texture="brick", collider="box", scale=Vec3(1, 3, 5), position=Vec3(-5, 1.5, 0), texture_scale=Vec2(5, 3))
    wall_2_collider = AABB(Vec3(-5, 1.5, 0), Vec3(0, 0, 0), Vec3(1, 3, 5))

    wall_3 = Entity(model="cube", texture="brick", collider="box", scale=Vec3(5, 3, 1), position=Vec3(0, 1.5, 5), texture_scale=Vec2(5, 3))
    wall_3_collider = AABB(Vec3(0, 1.5, 5), Vec3(0, 0, 0), Vec3(5, 3, 1))

    wall_4 = Entity(model="cube", texture="brick", collider="box", scale=Vec3(5, 3, 1), position=Vec3(0, 1.5, -5), texture_scale=Vec2(5, 3))
    wall_4_collider = AABB(Vec3(0, 1.5, -5), Vec3(0, 0, 0), Vec3(5, 3, 1))

    ceiling = Entity(model="cube", texture="brick", scale=Vec3(11, 1, 11), position=Vec3(0, 3.5, 0), texture_scale=Vec2(11, 11))
    ceiling_collider = AABB(Vec3(0, 3.5, 0), Vec3(0, 0, 0), Vec3(11, 1, 11))

    colliders = [ground_collider, wall_1_collider, wall_2_collider, wall_3_collider, wall_4_collider, ceiling_collider]

    player = Player(colliders, position=Vec3(0, 2.5, 0))


    def input(key):
        if key == "escape":
            mouse.locked = not mouse.locked

        if key == "n":
            player.noclip_mode = not player.noclip_mode


    app.run()
