#ifndef Telemetry_H
#define Telemetry_H

#include "vec3.h"

typedef struct 
{
    double sx, sy, sz;
    double gx, gy, gz;
    double lx, ly, lz;
    double slant_range;
    double incidence_angle;
    double doppler_hz;
    double velocity_kms;
    double period_s;

} Telemetry;

Telemetry compute_telemetry(
    double a, double e, double i,
    double raan, double omega, double nu,
    double altitude, double wavelength, double squint_angle,
    Vec3 ground);

Telemetry compute_telemetry(
    double a, double e, double i, double raan, double omega, double nu, 
    double altitude, double wavelength, double squint_angle,
    Vec3 ground
);

#endif