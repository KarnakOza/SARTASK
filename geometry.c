#include <math.h>
#include "constants.h"

double slant_range_from_altitude(double altitude, double incidence_angle)
{
    double r = EARTH_RADIUS + altitude;
    return r / cos(incidence_angle);
}