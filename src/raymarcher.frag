#version 150

uniform mat4 p3d_ProjectionMatrixInverse;
uniform mat4 p3d_ViewMatrixInverse;
uniform int osg_FrameNumber;
uniform vec2 u_resolution;

out vec4 p3d_FragColor;

const int MAX_STEPS = 256;
const float MAX_DIST = 500.0;
const float EPSILON = 0.001;


vec2 get_union(vec2 object_1, vec2 object_2) {
    return (object_1.x < object_2.x) ? object_1 : object_2;
}


vec2 get_union_round(vec2 object_1, vec2 object_2) {
    float r = 0.5;

    vec2 u = max(vec2(r - object_1.x,r - object_2.x), vec2(0));
    float dist = max(r, min (object_1.x, object_2.x)) - length(u);

    return (object_1.x < object_2.x) ? vec2(dist, object_1.y) : vec2(dist, object_2.y);
}


vec2 scene(vec3 point) {
    vec3 q_1 = abs(point + vec3(0.0, 0.5 * sin(0.02 * osg_FrameNumber), 0.0)) - 0.2;
    float cube_dist_1 = length(max(q_1,0.0)) + min(max(q_1.x,max(q_1.y,q_1.z)),0.0) - .2;
    vec2 cube_1 = vec2(cube_dist_1, 1.0);

    vec3 q_2 = abs(point + vec3(0.0, -1.0, 0.0)) - 0.2;
    float cube_dist_2 = length(max(q_2,0.0)) + min(max(q_2.x,max(q_2.y,q_2.z)),0.0) - .2;
    vec2 cube_2 = vec2(cube_dist_2, 1.0);

    float plane_dist = dot(point, vec3(0.0, 1.0, 0.0)) + 1.0;
    vec2 plane = vec2(plane_dist, 2.0);

    return get_union(get_union_round(cube_1, cube_2), plane);
}


vec2 ray_march(vec3 position, vec3 direction) {
    vec2 hit, object;

    for (int i = 0; i < MAX_STEPS; i++) {
        hit = scene(position + object.x * direction);

        object.x += hit.x;
        object.y = hit.y;

        if (hit.x < EPSILON || object.x > MAX_DIST) {
            break;
        }
    }
    return object;
}


vec3 get_normal(vec3 point) {
    vec2 e = vec2(EPSILON, 0.0);
    vec3 normal = vec3(scene(point).x) - vec3(scene(point - e.xyy).x, scene(point - e.yxy).x, scene(point - e.yyx).x);
    return normalize(normal);
}


vec3 get_light(vec3 point, vec3 direction) {
    vec3 light_position = vec3(20.0, 40.0, -30.0);
    vec3 ambient_color = vec3(.2, .2, .25);
    vec3 light_color = vec3(1., 1., .8);
    vec3 specular_color = vec3(0.8, 1.0, 0.8);
    float specular_strength = 0.5;

    vec3 normal = get_normal(point);
    vec3 light_direction = normalize(light_position - point);
    vec3 reflect_direcion = reflect(-light_direction, normal);

    vec3 diffuse_light = max(dot(normal, light_direction), 0) * light_color;

    vec3 specular_light = specular_strength * pow(max(dot(reflect_direcion, -direction), 0.0), 24.0) * specular_color;

    vec2 object = ray_march(point + normal * 0.02, normalize(light_position));
    if (object.x < length(light_position - point)) return ambient_color;

    return ambient_color + diffuse_light + specular_light;
}


vec3 get_material(float id) {
    vec3 material;

    switch (int(id)) {
        case 1:
        material = vec3(0.9, 0.0, 0.0); break;
        case 2:
        material = vec3(0.2, 0.9, 0.0); break;
    }
    return material;
}


void main() {
    vec3 color;
    vec3 background = vec3(0.5, 0.8, 0.9);

    vec3 camera_position = p3d_ViewMatrixInverse[3].xyz / p3d_ViewMatrixInverse[3].w;

    vec2 uv = (gl_FragCoord.xy / u_resolution.xy) * 2.0 - 1.0;
    vec4 target = p3d_ProjectionMatrixInverse * vec4(uv, 1.0, 1.0);
    vec3 direction = vec3(p3d_ViewMatrixInverse * vec4(normalize(target.xyz / target.w), 0.0));

    vec2 object = ray_march(camera_position, direction);

    if (object.x < MAX_DIST) {
        vec3 point = camera_position + object.x * direction;
        color = get_material(object.y) * get_light(point, direction);
        color = mix(color, background, 1.0 - exp(-0.0002 * object.x * object.x));
    }

    else {
        color = background - max(0.95 * direction.y, 0.0);
    }

    color = pow(color, vec3(0.4545));
    p3d_FragColor = vec4(color, 1.0);
}
