#include <math.h>
#include "sar_range.h"

double slant_range(double xs, double ys, double zs,
                   double xg, double yg, double zg)
{
    double dx = xs - xg;
    double dy = ys - yg;
    double dz = zs - zg;

    return sqrt(dx*dx + dy*dy + dz*dz);
}
