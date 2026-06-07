from sgp4.api import Satrec, jday
from datetime import datetime, timezone, timedelta
import math


def propagate(satellite, hours=72, step_seconds=60):
    """
    Propagates a satellite forward in time using SGP4.
    
    Takes a Satellite object, returns a list of state vectors:
    each entry is a dict with time, position (ECI), velocity (ECI).

    Args:
        satellite   : Satellite object with line1, line2
        hours       : how far ahead to propagate (default 72)
        step_seconds: time resolution in seconds (default 60 = 1 min)

    Returns:
        list of dicts: [{time, x, y, z, vx, vy, vz}, ...]
    """

    # Build SGP4 satellite record from your TLE lines
    sat = Satrec.twoline2rv(satellite.line1, satellite.line2)

    # Start from right now (UTC)
    start_time = datetime.now(timezone.utc)

    states = []
    total_steps = int(hours * 3600 / step_seconds)

    for step in range(total_steps):

        # Current time for this step
        t = start_time + timedelta(seconds=step * step_seconds)

        # Convert to Julian date — what SGP4 needs
        jd, fr = jday(t.year, t.month, t.day,
                      t.hour, t.minute, t.second + t.microsecond * 1e-6)

        # SGP4 propagation — returns position and velocity in ECI (km, km/s)
        error, position, velocity = sat.sgp4(jd, fr)

        # error = 0 means success
        if error != 0:
            continue

        states.append({
            "time" : t,
            "x"    : position[0],   # ECI X in km
            "y"    : position[1],   # ECI Y in km
            "z"    : position[2],   # ECI Z in km
            "vx"   : velocity[0],   # velocity X in km/s
            "vy"   : velocity[1],
            "vz"   : velocity[2],
            "speed": math.sqrt(velocity[0]**2 + velocity[1]**2 + velocity[2]**2)
        })

    return states


def eci_to_latlon(x, y, z, time):
    """
    Converts ECI coordinates to latitude and longitude.
    
    Earth rotates — so we account for Greenwich Sidereal Time (GMST)
    to find which longitude is under the satellite right now.
    """
    # GMST — Earth's rotation angle at this moment
    # J2000 epoch: Jan 1 2000 12:00 UTC
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    seconds_since_j2000 = (time - j2000).total_seconds()

    # Earth rotates 360° in 86164 seconds (sidereal day)
    earth_rotation_rate = 2 * math.pi / 86164.0
    gmst = (earth_rotation_rate * seconds_since_j2000) % (2 * math.pi)

    # Rotate ECI to ECEF
    x_ecef =  x * math.cos(gmst) + y * math.sin(gmst)
    y_ecef = -x * math.sin(gmst) + y * math.cos(gmst)
    z_ecef =  z

    # ECEF to latitude/longitude
    r       = math.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)
    lat     = math.degrees(math.asin(z_ecef / r))
    lon     = math.degrees(math.atan2(y_ecef, x_ecef))
    alt     = r - 6371.0

    return lat, lon, alt


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), "."))
    from tle_parser import parse_tle
    from satellite import Satellite

    # Load and build satellite
    tle_data = parse_tle("data/tle/sentinel1.txt")
    first    = list(tle_data.keys())[0]
    elements = tle_data[first]

    sat = Satellite(
        name         = first,
        line1        = elements["line1"],
        line2        = elements["line2"],
        inclination  = elements["inclination"],
        raan         = elements["raan"],
        eccentricity = elements["eccentricity"],
        mean_motion  = elements["mean_motion"]
    )

    print(f"Propagating {sat.name} for 2 hours...")
    states = propagate(sat, hours=2, step_seconds=60)

    print(f"Total positions computed: {len(states)}")
    print(f"\nFirst position:")
    s = states[0]
    lat, lon, alt = eci_to_latlon(s["x"], s["y"], s["z"], s["time"])
    print(f"  Time : {s['time'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  ECI  : x={s['x']:.2f} y={s['y']:.2f} z={s['z']:.2f} km")
    print(f"  Lat  : {lat:.4f}°")
    print(f"  Lon  : {lon:.4f}°")
    print(f"  Alt  : {alt:.2f} km")
    print(f"  Speed: {s['speed']:.4f} km/s")