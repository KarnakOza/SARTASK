#include <stdio.h>
#include <math.h>

double doppler_centroid(double velocity, double wavelength, double angle)
{
    return (2 * velocity * 1000 / wavelength) * sin(angle);
}