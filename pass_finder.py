import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from propagator import propagate, eci_to_latlon
from sar_engine import get_slant_range, get_orbital_velocity


def elevation_angle(sat_x, sat_y, sat_z, tgt_x, tgt_y, tgt_z):
    """
    Computes elevation angle of satellite as seen from the target.
    
    Elevation = 0°  means satellite is on the horizon
    Elevation = 90° means satellite is directly overhead (nadir)
    
    A pass is visible when elevation > MIN_ELEVATION (we use 5°)
    """
    # Vector from target to satellite
    dx = sat_x - tgt_x
    dy = sat_y - tgt_y
    dz = sat_z - tgt_z

    # Target position is also its surface normal (Earth is a sphere)
    tgt_mag = math.sqrt(tgt_x**2 + tgt_y**2 + tgt_z**2)
    tgt_nx  = tgt_x / tgt_mag
    tgt_ny  = tgt_y / tgt_mag
    tgt_nz  = tgt_z / tgt_mag

    # Range to satellite
    range_mag = math.sqrt(dx**2 + dy**2 + dz**2)

    # Dot product of look vector and surface normal
    dot = dx*tgt_nx + dy*tgt_ny + dz*tgt_nz

    # Elevation angle
    el = math.degrees(math.asin(dot / range_mag))
    return el


def incidence_angle(sat_x, sat_y, sat_z, tgt_x, tgt_y, tgt_z):
    """
    Incidence angle = angle between incoming radar wave
    and the surface normal at the target.
    
    Radar wave travels FROM satellite TO target.
    Surface normal points OUTWARD from Earth center.
    For a satellite above the horizon, this angle is 0-90°.
    """
    # Look vector: FROM satellite TO target
    dx = tgt_x - sat_x
    dy = tgt_y - sat_y
    dz = tgt_z - sat_z
    look_mag = math.sqrt(dx**2 + dy**2 + dz**2)

    # Surface normal at target = outward radial direction
    tgt_mag = math.sqrt(tgt_x**2 + tgt_y**2 + tgt_z**2)
    nx = tgt_x / tgt_mag
    ny = tgt_y / tgt_mag
    nz = tgt_z / tgt_mag

    # Dot product of look direction (normalized) with surface normal
    dot = (dx/look_mag)*nx + (dy/look_mag)*ny + (dz/look_mag)*nz

    # dot is negative when satellite is above horizon
    # acos(-dot) gives the incidence angle correctly
    inc = math.degrees(math.acos(-dot))
    return inc


def score_pass(inc_angle, elevation, duration_minutes):
    """
    Scores a SAR pass from 0-100.
    
    This is your ranking engine — the core of SARTASK.
    Higher score = better imaging opportunity.
    
    Scoring logic:
    - Incidence angle 30-45° scores highest (optimal SAR geometry)
    - Higher elevation = longer imaging window
    - Longer duration = more imaging opportunity
    """
    # Incidence angle score (0-50 points)
    # Peak at 37.5° (midpoint of optimal 25-50° range)
    inc_optimal = 37.5
    inc_score = max(0, 50 - abs(inc_angle - inc_optimal) * 2)

    # Elevation score (0-30 points)
    el_score = min(30, elevation * 0.5)

    # Duration score (0-20 points)
    dur_score = min(20, duration_minutes * 2)

    total = inc_score + el_score + dur_score
    return round(total, 1)


def find_passes(satellite, target, hours=72, min_elevation=5.0):
    """
    Finds all passes of a satellite over a target in the next N hours.
    
    A pass starts when elevation > min_elevation
    and ends when elevation drops back below min_elevation.
    
    Returns a list of passes, each with:
    - start/end/peak time
    - max elevation
    - incidence angle at peak
    - duration
    - quality score
    """

    print(f"  Computing passes for {satellite.name} over {target.name}...")
    states = propagate(satellite, hours=hours, step_seconds=30)

    passes     = []
    in_pass    = False
    pass_start = None
    pass_states = []

    for state in states:
    # Earth rotation angle at this timestamp (GMST)
        from datetime import datetime, timezone
        j2000    = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        seconds  = (state["time"] - j2000).total_seconds()
        gmst     = (seconds * 2 * math.pi / 86164.0) % (2 * math.pi)

        # Rotate ECI directly to ECEF — no lat/lon roundtrip
        sat_ex =  state["x"] * math.cos(gmst) + state["y"] * math.sin(gmst)
        sat_ey = -state["x"] * math.sin(gmst) + state["y"] * math.cos(gmst)
        sat_ez =  state["z"]

        el = elevation_angle(sat_ex, sat_ey, sat_ez,
                            target.x, target.y, target.z)

        if el >= min_elevation:
            if not in_pass:
                in_pass    = True
                pass_start = state["time"]
                pass_states = []
            pass_states.append((state, el, sat_ex, sat_ey, sat_ez))

        else:
            if in_pass:
            # rest of your pass processing stays exactly the same
                in_pass = False

                # Find peak elevation moment
                peak = max(pass_states, key=lambda x: x[1])
                peak_state, peak_el, px, py, pz = peak

                inc = incidence_angle(px, py, pz,
                                      target.x, target.y, target.z)

                duration = len(pass_states) * 30 / 60  # minutes

                score = score_pass(inc, peak_el, duration)

                passes.append({
                    "satellite"   : satellite.name,
                    "target"      : target.name,
                    "start"       : pass_start,
                    "end"         : state["time"],
                    "peak_time"   : peak_state["time"],
                    "max_elevation": round(peak_el, 2),
                    "incidence"   : round(inc, 2),
                    "duration_min": round(duration, 1),
                    "score"       : score,
                    "speed_kms"   : round(peak_state["speed"], 4)
                })

    return passes


def print_passes(passes):
    """Prints a formatted pass report to the terminal."""

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

    # Load Sentinel-1A
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

    # Your two key targets
    okmok = Target("Okmok Volcano",      53.43, -168.13,
                   "Alaska — high latitude")
    nyiragongo = Target("Nyiragongo Volcano", -1.52,  29.25,
                        "DR Congo — equatorial")

    # Find and print passes for both
    for target in [okmok, nyiragongo]:
        passes = find_passes(sat, target, hours=72)
        print_passes(passes)