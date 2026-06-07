#include "telemetry.h"
#include <math.h>
#include "constants.h"
#include "vec3.h"

/* Function declaration */

Vec3 satellite_position_eci(double, double, double, double, double, double);
double orbital_velocity(double);
double orbital_period(double);
double doppler_centroid(double, double, double);

Telemetry compute_telemetry(
    double a, double e, double i, double raan, double omega, double nu,
    double altitude, double wavelength, double squint_angle,
    Vec3 ground)

{
    Telemetry t;

    Vec3 sat = satellite_position_eci(a, e, i, raan, omega, nu);
    Vec3 look = vec3_sub(ground, sat);

    
    t.sx = sat.x;
    t.sy = sat.y;
    t.sz = sat.z;

    t.gx = ground.x;
    t.gy = ground.y;
    t.gz = ground.z;

    t.lx = look.x;
    t.ly = look.y;
    t.lz = look.z;


    t.slant_range = vec3_norm(look);

    Vec3 normal = vec3_normalize(ground);

    double dot = vec3_dot(look, normal);

    t.incidence_angle = acos(dot / (vec3_norm(look) * vec3_norm(normal))) * 180.0 / PI;

    t.velocity_kms = orbital_velocity(altitude);
    t.period_s = orbital_period(altitude);
    // t.doppler_hz = doppler_centroid(t.velocity_kms, wavelength, squint_angle);

    
    Vec3 velocity_dir = vec3_normalize(sat); // approx orbital direction
    
    Vec3 look_dir = vec3_normalize(look);

    double cos_theta = vec3_dot(velocity_dir, look_dir);

    t.doppler_hz = (2.0 * t.velocity_kms / wavelength) * cos_theta;

    return t;
}