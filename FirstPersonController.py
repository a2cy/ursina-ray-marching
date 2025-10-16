from ursina import Entity, Vec3, time, held_keys, camera, mouse, lerp, clamp


class AABBCollider:
    def __init__(self, position: Vec3, origin: Vec3, scale: Vec3) -> None:
        self._half_scale = scale / 2
        self._origin = origin
        self.position = position

    @property
    def position(self) -> Vec3:
        return self._position

    @position.setter
    def position(self, value: Vec3) -> None:
        self._position = value

        self.x_1 = value.x + self._origin.x - self._half_scale.x
        self.y_1 = value.y + self._origin.y - self._half_scale.y
        self.z_1 = value.z + self._origin.z - self._half_scale.z

        self.x_2 = value.x + self._origin.x + self._half_scale.x
        self.y_2 = value.y + self._origin.y + self._half_scale.y
        self.z_2 = value.z + self._origin.z + self._half_scale.z

    def intersect(self, collider) -> tuple:
        x_max = self.x_1 - collider.x_2
        x_min = collider.x_1 - self.x_2

        y_max = self.y_1 - collider.y_2
        y_min = collider.y_1 - self.y_2

        z_max = self.z_1 - collider.z_2
        z_min = collider.z_1 - self.z_2

        min_dist = max(x_max, x_min, y_max, y_min, z_max, z_min)

        if min_dist >= 0:
            return 1, None

        normal_x = (0, 1, -1, 0)[(min_dist == x_max) + (min_dist == x_min) * 2]
        normal_y = (0, 1, -1, 0)[(min_dist == y_max) + (min_dist == y_min) * 2]
        normal_z = (0, 1, -1, 0)[(min_dist == z_max) + (min_dist == z_min) * 2]

        return -min_dist, Vec3(normal_x, normal_y, normal_z)

    def collide(self, collider, move_delta: Vec3) -> tuple:
        def get_time(x: float, y: float) -> float:
            return x / y if y else float("-" * (x > 0) + "inf")

        x_entry = get_time(collider.x_1 - self.x_2 if move_delta.x > 0 else collider.x_2 - self.x_1, move_delta.x)
        x_exit = get_time(collider.x_2 - self.x_1 if move_delta.x > 0 else collider.x_1 - self.x_2, move_delta.x)

        y_entry = get_time(collider.y_1 - self.y_2 if move_delta.y > 0 else collider.y_2 - self.y_1, move_delta.y)
        y_exit = get_time(collider.y_2 - self.y_1 if move_delta.y > 0 else collider.y_1 - self.y_2, move_delta.y)

        z_entry = get_time(collider.z_1 - self.z_2 if move_delta.z > 0 else collider.z_2 - self.z_1, move_delta.z)
        z_exit = get_time(collider.z_2 - self.z_1 if move_delta.z > 0 else collider.z_1 - self.z_2, move_delta.z)

        entry_time = max(x_entry, y_entry, z_entry)
        exit_time = min(x_exit, y_exit, z_exit)

        if entry_time > exit_time or entry_time > 1 or entry_time < 0:
            return 1, None

        normal_x = (0, -1 if move_delta.x > 0 else 1)[entry_time == x_entry]
        normal_y = (0, -1 if move_delta.y > 0 else 1)[entry_time == y_entry]
        normal_z = (0, -1 if move_delta.z > 0 else 1)[entry_time == z_entry]

        return entry_time, Vec3(normal_x, normal_y, normal_z)


class Player(Entity):
    def __init__(self, colliders: list, **kwargs) -> None:
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

        self.player_collider = AABBCollider(position=Vec3(0), origin=Vec3(0, -0.6, 0), scale=Vec3(0.8, 1.8, 0.8))
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

    def update(self) -> None:
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -89, 89)

        if self.noclip_mode:
            self.direction = Vec3(
                self.camera_pivot.forward * (held_keys["w"] - held_keys["s"]) + self.right * (held_keys["d"] - held_keys["a"])
            ).normalized()

            self.direction += self.up * (held_keys["e"] - held_keys["q"])

            self.velocity = lerp(self.direction * self.noclip_speed, self.velocity, 0.5 ** (self.noclip_acceleration * time.dt))

            self.position += self.velocity * time.dt

        else:
            if self.grounded and held_keys["space"]:
                self.velocity.y = (self.gravity * self.jump_height * 2) ** 0.5

            self.direction = Vec3(self.forward * (held_keys["w"] - held_keys["s"]) + self.right * (held_keys["d"] - held_keys["a"])).normalized()

            if held_keys["left shift"]:
                self.direction *= self.sprint_multiplier
                camera.fov = lerp(self.fov * self.fov_multiplier, camera.fov, 0.5 ** (self.acceleration * time.dt))

            else:
                camera.fov = lerp(self.fov, camera.fov, 0.5 ** (self.acceleration * time.dt))

            self.velocity.xz = lerp(self.direction * self.walk_speed, self.velocity, 0.5 ** (self.acceleration * time.dt)).xz
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
                    move_delta.x = move_delta.x * collision_time

                if normal.y:
                    self.velocity.y = 0
                    move_delta.y = move_delta.y * collision_time

                if normal.z:
                    self.velocity.z = 0
                    move_delta.z = move_delta.z * collision_time

                if normal.y == 1:
                    self.grounded = True

            for _ in range(3):
                collisions = []

                self.player_collider.position = self.position + move_delta

                for collider in self.colliders:
                    min_dist, normal = self.player_collider.intersect(collider)

                    if normal is None:
                        continue

                    collisions.append((min_dist, normal))

                if not collisions:
                    break

                min_dist, normal = min(collisions, key=lambda x: x[0])

                if normal.x:
                    self.velocity.x = 0
                    move_delta.x = min_dist * normal.x

                if normal.y:
                    self.velocity.y = 0
                    move_delta.y = min_dist * normal.y

                if normal.z:
                    self.velocity.z = 0
                    move_delta.z = min_dist * normal.z

            self.position += move_delta

    def on_enable(self) -> None:
        mouse.position = Vec3(0)
        mouse.locked = True

    def on_disable(self) -> None:
        mouse.locked = False


if __name__ == "__main__":
    from ursina import Ursina, Vec2

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
