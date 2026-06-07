#include <math.h>
#include "vec3.h"

Vec3 vec3_add(Vec3 a, Vec3 b)
{
    Vec3 r;
    r.x = a.x + b.x;
    r.y = a.y + b.y;
    r.z = a.z + b.z;
    return r;
}

Vec3 vec3_sub(Vec3 a, Vec3 b)
{
    Vec3 r;
    r.x = a.x - b.x;
    r.y = a.y - b.y;
    r.z = a.z - b.z;
    return r;
}

double vec3_dot(Vec3 a, Vec3 b)
{
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

double vec3_norm(Vec3 v)
{
    return sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
}

Vec3 vec3_normalize(Vec3 v)
{
    double mag = vec3_norm(v);

    Vec3 result;
    if (mag == 0.0)
    {
        result.x = 0;
        result.y = 0;
        result.z = 0;
    }
    else
    {
        result.x = v.x / mag;
        result.y = v.y / mag;
        result.z = v.z / mag;
    }
    return result;
}