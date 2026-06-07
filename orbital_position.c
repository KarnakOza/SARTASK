#include <stdio.h>
#include <math.h>
#include "constants.h"

void satellite_position(double a, double e, double true_anomaly,
                            double *x, double *y)
{
    double r;

    r = (a * (1 - e * e)) / (1 + e * cos(true_anomaly));

    *x = r * cos(true_anomaly);
    *y = r * sin(true_anomaly);
}