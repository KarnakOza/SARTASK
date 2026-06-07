import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from tle_parser import parse_tle


class Satellite:

    def __init__(self, name, line1, line2, inclination,
                 raan, eccentricity, mean_motion):
        self.name         = name
        self.line1        = line1
        self.line2        = line2
        self.inclination  = inclination
        self.raan         = raan
        self.eccentricity = eccentricity
        self.mean_motion  = mean_motion

    def orbital_period(self):
        return 1440 / self.mean_motion

    def semi_major_axis(self):
        mu = 398600.4418
        n  = self.mean_motion * 2 * math.pi / 86400
        a  = (mu / n**2) ** (1/3)
        return a

    def altitude(self):
        earth_radius = 6371.0
        return self.semi_major_axis() - earth_radius

    def is_sun_synchronous(self):
        return 96.0 <= self.inclination <= 100.0

    def summary(self):
        print(f"\n{'='*45}")
        print(f"  SATELLITE : {self.name}")
        print(f"{'='*45}")
        print(f"  Inclination    : {self.inclination}°")
        print(f"  RAAN           : {self.raan}°")
        print(f"  Eccentricity   : {self.eccentricity}")
        print(f"  Mean Motion    : {self.mean_motion} rev/day")
        print(f"  Orbital Period : {self.orbital_period():.2f} min")
        print(f"  Semi-major axis: {self.semi_major_axis():.2f} km")
        print(f"  Altitude       : {self.altitude():.2f} km")
        print(f"  Sun-Synchronous: {self.is_sun_synchronous()}")
        print(f"{'='*45}")


# ← THIS LINE HAS ZERO INDENTATION. It is outside the class.
if __name__ == "__main__":

    tle_data = parse_tle("data/tle/sentinel1.txt")

    satellites = []
    for name, elements in tle_data.items():
        sat = Satellite(
            name         = name,
            line1        = elements["line1"],
            line2        = elements["line2"],
            inclination  = elements["inclination"],
            raan         = elements["raan"],
            eccentricity = elements["eccentricity"],
            mean_motion  = elements["mean_motion"]
        )
        satellites.append(sat)

    for sat in satellites:
        sat.summary()