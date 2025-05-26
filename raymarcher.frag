#version 150

uniform mat4 p3d_ViewMatrixInverse;

uniform vec3 u_light_position;
uniform sampler2D u_texture;
uniform float u_time;

in vec3 fragcoord;

out vec4 p3d_FragColor;

const int MAX_STEPS = 256;
const float MAX_DIST = 128.0;
const float EPSILON = 0.0001;
const float TRIPLINAR_SCALE = 1;


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
    float sphere_dist = length(point + vec3(0.0 + 1.2 * sin(4 * u_time), 0.0, 0.0)) - 0.4;
    vec2 sphere = vec2(sphere_dist, 1.0);

    vec3 q_1 = abs(point + vec3(0.0, 0.0, 0.0)) - 0.2;
    float cube_dist_1 = length(max(q_1,0.0)) + min(max(q_1.x,max(q_1.y,q_1.z)),0.0) - 0.2;
    vec2 cube_1 = vec2(cube_dist_1, 1.0);

    vec3 q_2 = abs(point + vec3(0.0, -0.8, -2.0)) - 0.5;
    float cube_dist_2 = length(max(q_2,0.0)) + min(max(q_2.x,max(q_2.y,q_2.z)),0.0);
    vec2 cube_2 = vec2(cube_dist_2, 3.0);

    float plane_dist = dot(point, vec3(0.0, 1.0, 0.0)) + 1.0;
    vec2 plane = vec2(plane_dist, 2.0);

    return get_union(get_union(get_union_round(sphere, cube_1), cube_2), plane);;
}


vec2 ray_march(vec3 position, vec3 direction) {
    vec2 object;

    for (int i = 0; i < MAX_STEPS; i++) {
        vec2 hit = scene(position + object.x * direction);

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


float get_shadow(vec3 point, vec3 direction, float distance) {
    float res = 1.0;
    float dist = 0.0;

    for (int i = 0; i < MAX_STEPS; i++) {
        vec2 hit = scene(point + dist * direction);
        res = min(res, 16.0 * hit.x / dist);
        dist += hit.x;

        if (hit.x < EPSILON || dist > distance) {
            break;
        }
    }

    if (dist < distance) {
        return 0.0;
    }

    return res;
}


vec4 get_light(vec3 point, vec3 normal, vec3 view_direction, vec4 color) {
    vec4 ambient_color = vec4(0.2, 0.2, 0.25, 1.0);
    vec4 light_color = vec4(1.0, 1.0, 0.95, 1.0);

    vec3 light_direction = normalize(u_light_position - point);
    vec3 half_direction = normalize(light_direction + view_direction);

    vec4 ambient_light = ambient_color * color;
    vec4 diffuse_light = max(dot(normal, light_direction), 0.0) * color * light_color;
    vec4 specular_light = 0.25 * pow(max(dot(normal, half_direction), 0.0), 32.0) * light_color;

    float light_contib = get_shadow(point + normal * 0.05, light_direction, length(u_light_position - point));

    return ambient_light + (diffuse_light + specular_light) * light_contib;
}


vec4 triplanar(vec3 point, vec3 normal, sampler2D texture_map) {
    vec4 dx = texture(texture_map, vec2(point.zy / TRIPLINAR_SCALE));
    vec4 dy = texture(texture_map, vec2(point.xz / TRIPLINAR_SCALE));
    vec4 dz = texture(texture_map, vec2(point.xy / TRIPLINAR_SCALE));

    vec3 weights = abs(normal.xyz);
    weights = weights / (weights.x + weights.y + weights.z);

    return dx * weights.x + dy * weights.y + dz * weights.z;
}


vec4 get_material(float id, vec3 point, vec3 normal) {
    vec4 color;

    switch (int(id)) {
        case 1:
        color = vec4(abs(sin(1.5 * u_time)), 0.0, abs(cos(1.5 * u_time)), 1.0); break;
        case 2:
        color = vec4(vec3(0.2 + 0.4 * mod(floor(point.x) + floor(point.z), 2.0)), 1.0); break;
        case 3:
        color = triplanar(point, normal, u_texture); break;
    }
    return color;
}


void main() {
    vec4 color = vec4(0);

    vec3 camera_position = p3d_ViewMatrixInverse[3].xyz / p3d_ViewMatrixInverse[3].w;

    vec3 ray_direction = normalize(fragcoord - camera_position);

    vec2 object = ray_march(camera_position, ray_direction);

    if (object.x < MAX_DIST) {
        vec3 point = camera_position + object.x * ray_direction;
        vec3 normal = get_normal(point);

        color = get_light(point, normal, -ray_direction, get_material(object.y, point, normal));
        color = mix(color, vec4(0), 1.0 - exp(-0.0008 * object.x * object.x));
    }

    else {
        discard;
    }

    p3d_FragColor = color.rgba;
}
