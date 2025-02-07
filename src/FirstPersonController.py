from ursina import *


class AABB:

    def __init__(self, position, origin, scale):
        self._scale = scale
        self._origin = origin
        self.position = position


    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

        self.x_1 = value.x + self._origin.x - self._scale.x / 2
        self.y_1 = value.y + self._origin.y - self._scale.y / 2
        self.z_1 = value.z + self._origin.z - self._scale.z / 2

        self.x_2 = value.x + self._origin.x + self._scale.x / 2
        self.y_2 = value.y + self._origin.y + self._scale.y / 2
        self.z_2 = value.z + self._origin.z + self._scale.z / 2


class Player(Entity):

    def __init__(self, colliders, **kwargs):
        super().__init__(**kwargs)

        self.walk_speed = 6
        self.acceleration = 16
        self.sprint_multiplier = 1.6

        self.gravity = 25
        self.jump_height = 1.2
        self.grounded = False

        self.noclip_speed = 24
        self.noclip_acceleration = 6
        self.noclip_mode = False

        self.player_collider = AABB(Vec3(0), Vec3(0, -.6, 0), Vec3(.8, 1.8, .8))
        self.colliders = colliders

        self.fov = 90
        self.fov_multiplier = 1.12
        self.camera_pivot = Entity(parent=self)
        camera.parent = self.camera_pivot
        camera.position = Vec3(0)
        camera.rotation = Vec3(0)
        camera.fov = self.fov
        self.mouse_sensitivity = 80

        self.direction = Vec3(0)
        self.velocity = Vec3(0)


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
            return 1, Vec3(0)

        if x_entry > 1 or y_entry > 1 or z_entry > 1:
            return 1, Vec3(0)

        entry_time = max(x_entry, y_entry, z_entry)
        exit_time = min(x_exit, y_exit, z_exit)

        if entry_time > exit_time:
            return 1, Vec3(0)

        normal_x = (0, -1 if direction.x > 0 else 1)[entry_time == x_entry]
        normal_y = (0, -1 if direction.y > 0 else 1)[entry_time == y_entry]
        normal_z = (0, -1 if direction.z > 0 else 1)[entry_time == z_entry]

        return entry_time, Vec3(normal_x, normal_y, normal_z)


    def update(self):
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -89, 89)

        if self.noclip_mode:
            self.direction = Vec3(self.camera_pivot.forward * (held_keys["w"] - held_keys["s"])
                              + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            self.direction += self.up * (held_keys["e"] - held_keys["q"])

            self.velocity = lerp(self.velocity, self.direction * self.noclip_speed, self.noclip_acceleration * min(time.dt, .05))

        else:
            if self.grounded and held_keys["space"]:
                self.velocity.y = (self.gravity * self.jump_height * 2)**.5

            self.direction = Vec3(self.forward * (held_keys["w"] - held_keys["s"])
                                  + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            if held_keys["left shift"]:
                self.direction *= self.sprint_multiplier
                camera.fov = lerp(camera.fov, self.fov * self.fov_multiplier, self.acceleration * min(time.dt, .05))

            else:
                camera.fov = lerp(camera.fov, self.fov, self.acceleration * min(time.dt, .05))

            self.velocity.xz = lerp(self.velocity, self.direction * self.walk_speed, self.acceleration * min(time.dt, .05)).xz
            self.velocity.y = self.velocity.y - self.gravity * time.dt

            self.grounded = False

            self.player_collider.position = self.position

            for _ in range(3):
                velocity = self.velocity * time.dt
                collisions = []

                for collider in self.colliders:
                    if self.aabb_broadphase(self.player_collider, collider, velocity):
                        collision_time, collision_normal = self.swept_aabb(self.player_collider, collider, velocity)

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

        self.player_collider.position = self.position


    def on_enable(self):
        mouse.position = Vec3(0)
        mouse.locked = True


    def on_disable(self):
        mouse.locked = False


if __name__ == "__main__":
    app = Ursina(borderless=False)

    ground = Entity(model="plane", texture="grass", scale=Vec3(100, 1, 100), texture_scale=Vec2(100, 100))
    ground_collider = AABB(ground.position, Vec3(0, -.5, 0), ground.scale)

    wall = Entity(model="cube", texture="brick", scale=Vec3(1, 3, 5), position=Vec3(5, 1.5, 0), texture_scale=Vec2(5, 3))
    wall_collider = AABB(wall.position, Vec3(0), wall.scale)

    box = Entity(model="cube", texture="brick", scale=Vec3(1), position=Vec3(3.5, .5, 0))
    box_collider = AABB(box.position, Vec3(0), box.scale)

    ceiling = Entity(model="cube", texture="brick", scale=Vec3(2, 1, 5), position=Vec3(6.5, 3, 0), texture_scale=Vec2(2, 5))
    ceiling_collider = AABB(ceiling.position, Vec3(0), ceiling.scale)

    colliders = [ground_collider, wall_collider, box_collider, ceiling_collider]

    player = Player(colliders, position=Vec3(0, 2.5, 0))

    def input(key):
        if key == "escape":
            player.enabled = not player.enabled

        if key == "n":
            player.noclip_mode = not player.noclip_mode


    app.run()
