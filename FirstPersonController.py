from ursina import *


class AABBCollider:

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


    def intersect(self, collider):
        return (self.x_1 < collider.x_2 and self.x_2 > collider.x_1 and
                self.y_1 < collider.y_2 and self.y_2 > collider.y_1 and
                self.z_1 < collider.z_2 and self.z_2 > collider.z_1)


    def collide(self, collider, direction):
        get_time = lambda x, y: x / y if y else float("-" * (x > 0) + "inf")

        no_collision = 1, None

        x_entry = get_time(collider.x_1 - self.x_2 if direction.x > 0 \
                           else collider.x_2 - self.x_1, direction.x)
        x_exit = get_time(collider.x_2 - self.x_1 if direction.x > 0 \
                          else collider.x_1 - self.x_2, direction.x)

        y_entry = get_time(collider.y_1 - self.y_2 if direction.y > 0 \
                           else collider.y_2 - self.y_1, direction.y)
        y_exit = get_time(collider.y_2 - self.y_1 if direction.y > 0 \
                          else collider.y_1 - self.y_2, direction.y)

        z_entry = get_time(collider.z_1 - self.z_2 if direction.z > 0 \
                           else collider.z_2 - self.z_1, direction.z)
        z_exit = get_time(collider.z_2 - self.z_1 if direction.z > 0 \
                          else collider.z_1 - self.z_2, direction.z)

        if x_entry < 0 and y_entry < 0 and z_entry < 0:
            return no_collision

        if x_entry > 1 or y_entry > 1 or z_entry > 1:
            return no_collision

        entry_time = max(x_entry, y_entry, z_entry)
        exit_time = min(x_exit, y_exit, z_exit)

        if entry_time > exit_time:
            return no_collision

        normal_x = (0, -1 if direction.x > 0 else 1)[entry_time == x_entry]
        normal_y = (0, -1 if direction.y > 0 else 1)[entry_time == y_entry]
        normal_z = (0, -1 if direction.z > 0 else 1)[entry_time == z_entry]

        return entry_time, Vec3(normal_x, normal_y, normal_z)


class Player(Entity):

    def __init__(self, colliders, **kwargs):
        super().__init__(**kwargs)

        self.gravity = 25
        self.walk_speed = 6
        self.max_fall_speed = 60
        self.acceleration = 16
        self.sprint_multiplier = 1.6
        self.jump_height = 1.2
        self.grounded = False

        self.noclip_speed = 24
        self.noclip_acceleration = 6
        self.noclip_mode = False

        self.player_collider = AABBCollider(Vec3(0), Vec3(0, -0.6, 0), Vec3(0.8, 1.8, 0.8))
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


    def update(self):
        floor_2d = lambda x: int(x * 100) / 100

        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -89, 89)

        if self.noclip_mode:
            self.direction = Vec3(self.camera_pivot.forward * (held_keys["w"] - held_keys["s"])
                              + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            self.direction += self.up * (held_keys["e"] - held_keys["q"])

            self.velocity = lerp(self.direction * self.noclip_speed, self.velocity, 0.5**(self.noclip_acceleration * time.dt))

            self.position += self.velocity * time.dt

        else:
            if self.grounded and held_keys["space"]:
                self.velocity.y = (self.gravity * self.jump_height * 2)**0.5

            self.direction = Vec3(self.forward * (held_keys["w"] - held_keys["s"])
                                  + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            if held_keys["left shift"]:
                self.direction *= self.sprint_multiplier
                camera.fov = lerp(self.fov * self.fov_multiplier, camera.fov, 0.5**(self.acceleration * time.dt))

            else:
                camera.fov = lerp(self.fov, camera.fov, 0.5**(self.acceleration * time.dt))

            self.velocity.xz = lerp(self.direction * self.walk_speed, self.velocity, 0.5**(self.acceleration * time.dt)).xz
            self.velocity.y = self.velocity.y - self.gravity * min(time.dt, 0.5)
            self.velocity.y = max(self.velocity.y, -self.max_fall_speed)

            self.grounded = False
            self.player_collider.position = self.position
            move_delta = self.velocity * time.dt

            for _ in range(3):
                collisions = []

                for collider in self.colliders:
                    collision_time, normal = self.player_collider.collide(collider, move_delta)

                    if normal is None:
                        continue

                    collisions.append((collision_time, normal))

                if not collisions:
                    break

                collision_time, normal = min(collisions, key=lambda x: x[0])

                if normal.x:
                    self.velocity.x = 0
                    move_delta.x = floor_2d(move_delta.x * collision_time)

                if normal.y:
                    self.velocity.y = 0
                    move_delta.y = floor_2d(move_delta.y * collision_time)

                if normal.z:
                    self.velocity.z = 0
                    move_delta.z = floor_2d(move_delta.z * collision_time)

                if normal.y == 1:
                    self.grounded = True

            self.position += move_delta

        self.player_collider.position = self.position


    def on_enable(self):
        mouse.position = Vec3(0)
        mouse.locked = True


    def on_disable(self):
        mouse.locked = False


if __name__ == "__main__":
    app = Ursina(borderless=False)

    ground = Entity(model="plane", texture="grass", scale=Vec3(100, 1, 100), texture_scale=Vec2(100, 100))
    ground_collider = AABBCollider(ground.position, Vec3(0, -0.5, 0), ground.scale)

    wall = Entity(model="cube", texture="brick", scale=Vec3(1, 3, 5), position=Vec3(5, 1.5, 0), texture_scale=Vec2(5, 3))
    wall_collider = AABBCollider(wall.position, Vec3(0), wall.scale)

    box = Entity(model="cube", texture="brick", scale=Vec3(1), position=Vec3(3.5, 0.5, 0))
    box_collider = AABBCollider(box.position, Vec3(0), box.scale)

    ceiling = Entity(model="cube", texture="brick", scale=Vec3(2, 1, 5), position=Vec3(6.5, 3, 0), texture_scale=Vec2(2, 5))
    ceiling_collider = AABBCollider(ceiling.position, Vec3(0), ceiling.scale)

    colliders = [ground_collider, wall_collider, box_collider, ceiling_collider]

    player = Player(colliders, position=Vec3(0, 25, 0))

    def input(key):
        if key == "escape":
            player.enabled = not player.enabled

        if key == "n":
            player.noclip_mode = not player.noclip_mode


    app.run()