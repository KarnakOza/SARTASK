#ifndef VEC3_H
#define VEC3_H

typedef struct 
{
    double x;
    double y;
    double z;
} Vec3;

Vec3 vec3_sub(Vec3 a, Vec3 b);
Vec3 vec3_normalize(Vec3 v);
double vec3_norm(Vec3 v);
double vec3_dot(Vec3, Vec3 b);

#endif
