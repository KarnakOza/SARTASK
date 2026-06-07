#include <math.h>

void eci_to_ecef(double x_eci, double y_eci, double z_eci,
                 double theta,
                 double *x_ecef, double *y_ecef, double *z_ecef)
{
    *x_ecef = cos(theta)*x_eci + sin(theta)*y_eci;
    *y_ecef = -sin(theta)*x_eci + cos(theta)*y_eci;
    *z_ecef = z_eci;
}
