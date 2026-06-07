import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from propagator import propagate, eci_to_latlon

# Pure Python physics — same formulas as C engine
# No ctypes/shared library needed on Streamlit Cloud
def _orbital_velocity(altitude_km):
    MU = 398600.4418
    r  = 6378.137 + altitude_km
    return math.sqrt(MU / r)

def _slant_range(sx, sy, sz, gx, gy, gz):
    return math.sqrt((sx-gx)**2 + (sy-gy)**2 + (sz-gz)**2)


def elevation_angle(sat_x, sat_y, sat_z, tgt_x, tgt_y, tgt_z):
    """
    Computes elevation angle of satellite as seen from the target.
    Elevation = 0°  means satellite is on the horizon
    Elevation = 90° means satellite is directly overhead (nadir)
    A pass is visible when elevation > MIN_ELEVATION (we use 5°)
    """
    dx = sat_x - tgt_x
    dy = sat_y - tgt_y
    dz = sat_z - tgt_z

    tgt_mag = math.sqrt(tgt_x**2 + tgt_y**2 + tgt_z**2)
    tgt_nx  = tgt_x / tgt_mag
    tgt_ny  = tgt_y / tgt_mag
    tgt_nz  = tgt_z / tgt_mag

    range_mag = math.sqrt(dx**2 + dy**2 + dz**2)
    dot       = dx*tgt_nx + dy*tgt_ny + dz*tgt_nz
    el        = math.degrees(math.asin(dot / range_mag))
    return el


def incidence_angle(sat_x, sat_y, sat_z, tgt_x, tgt_y, tgt_z):
    """
    Incidence angle = angle between incoming radar wave
    and the surface normal at the target.
    Radar wave travels FROM satellite TO target.
    Surface normal points OUTWARD from Earth center.
    For a satellite above the horizon, this angle is 0-90°.
    """
    dx = tgt_x - sat_x
    dy = tgt_y - sat_y
    dz = tgt_z - sat_z

    look_mag = math.sqrt(dx**2 + dy**2 + dz**2)

    tgt_mag = math.sqrt(tgt_x**2 + tgt_y**2 + tgt_z**2)
    nx = tgt_x / tgt_mag
    ny = tgt_y / tgt_mag
    nz = tgt_z / tgt_mag

    dot = (dx/look_mag)*nx + (dy/look_mag)*ny + (dz/look_mag)*nz
    inc = math.degrees(math.acos(-dot))
    return inc


def score_pass(inc_angle, elevation, duration_minutes):
    """
    Scores a SAR pass from 0-100.
    Higher score = better imaging opportunity.
    - Incidence angle 30-45° scores highest (optimal SAR geometry)
    - Higher elevation = longer imaging window
    - Longer duration = more imaging opportunity
    """
    inc_optimal = 37.5
    inc_score   = max(0, 50 - abs(inc_angle - inc_optimal) * 2)
    el_score    = min(30, elevation * 0.5)
    dur_score   = min(20, duration_minutes * 2)
    return round(inc_score + el_score + dur_score, 1)


def find_passes(satellite, target, hours=72, min_elevation=5.0):
    """
    Finds all passes of a satellite over a target in the next N hours.
    Returns a list of passes ranked by quality score.
    """
    print(f"  Computing passes for {satellite.name} over {target.name}...")
    states = propagate(satellite, hours=hours, step_seconds=30)

    passes     = []
    in_pass    = False
    pass_start = None
    pass_states = []

    for state in states:
        from datetime import datetime, timezone
        j2000   = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        seconds = (state["time"] - j2000).total_seconds()
        gmst    = (seconds * 2 * math.pi / 86164.0) % (2 * math.pi)

        # ECI → ECEF via GMST rotation
        sat_ex =  state["x"] * math.cos(gmst) + state["y"] * math.sin(gmst)
        sat_ey = -state["x"] * math.sin(gmst) + state["y"] * math.cos(gmst)
        sat_ez =  state["z"]

        el = elevation_angle(sat_ex, sat_ey, sat_ez,
                             target.x, target.y, target.z)

        if el >= min_elevation:
            if not in_pass:
                in_pass     = True
                pass_start  = state["time"]
                pass_states = []
            pass_states.append((state, el, sat_ex, sat_ey, sat_ez))

        else:
            if in_pass:
                in_pass = False

                peak = max(pass_states, key=lambda x: x[1])
                peak_state, peak_el, px, py, pz = peak

                inc      = incidence_angle(px, py, pz,
                                           target.x, target.y, target.z)
                duration = len(pass_states) * 30 / 60
                score    = score_pass(inc, peak_el, duration)

                passes.append({
                    "satellite"    : satellite.name,
                    "target"       : target.name,
                    "start"        : pass_start,
                    "end"          : state["time"],
                    "peak_time"    : peak_state["time"],
                    "max_elevation": round(peak_el, 2),
                    "incidence"    : round(inc, 2),
                    "duration_min" : round(duration, 1),
                    "score"        : score,
                    "speed_kms"    : round(peak_state["speed"], 4)
                })

    return passes


def print_passes(passes):
    if not passes:
        print("  No passes found.")
        return

    print(f"\n{'='*75}")
    print(f"  PASS QUALITY REPORT — {passes[0]['satellite']} → {passes[0]['target']}")
    print(f"{'='*75}")
    print(f"  {'#':<4} {'Start (UTC)':<22} {'Duration':>9} "
          f"{'Max El':>8} {'Incidence':>10} {'Score':>7}")
    print(f"  {'-'*68}")

    for i, p in enumerate(sorted(passes, key=lambda x: x["score"], reverse=True)):
        print(f"  {i+1:<4} "
              f"{p['start'].strftime('%Y-%m-%d %H:%M'):<22} "
              f"{p['duration_min']:>7.1f}m "
              f"{p['max_elevation']:>7.1f}° "
              f"{p['incidence']:>9.1f}° "
              f"{p['score']:>7.1f}")

    print(f"{'='*75}")
    print(f"  Total passes found : {len(passes)}")
    best = max(passes, key=lambda x: x["score"])
    print(f"  Best pass          : {best['start'].strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"  Best score         : {best['score']}/100")
    print(f"{'='*75}")


if __name__ == "__main__":
    from tle_parser import parse_tle
    from satellite import Satellite
    from target import Target

    tle_data = parse_tle("data/tle/satellites.txt")
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

    okmok      = Target("Okmok Volcano",      53.43, -168.13, "Alaska — high latitude")
    nyiragongo = Target("Nyiragongo Volcano", -1.52,   29.25, "DR Congo — equatorial")

    for target in [okmok, nyiragongo]:
        passes = find_passes(sat, target, hours=72)
        print_passes(passes)
