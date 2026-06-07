#include <stdio.h>
#include <math.h>
#include "constants.h"

double orbital_velocity(double altitude)
{
    double r = EARTH_RADIUS + altitude;
    return sqrt(MU / r);
}

double orbital_period(double altitude)
{
    double r = EARTH_RADIUS + altitude;
    return 2 * PI * sqrt(pow(r,3) / MU);
}