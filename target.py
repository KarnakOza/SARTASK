import math


class Target:
    """
    Represents a ground target to be imaged by a SAR satellite.
    Converts lat/lon to ECEF coordinates for geometry calculations.
    """

    EARTH_RADIUS = 6371.0

    def __init__(self, name, lat, lon, description=""):
        """
        Args:
            name        : target name e.g. "Okmok Volcano"
            lat         : latitude in degrees  (+N, -S)
            lon         : longitude in degrees (+E, -W)
            description : optional context
        """
        self.name        = name
        self.lat         = lat
        self.lon         = lon
        self.description = description

        # Convert to ECEF immediately on creation
        self.x, self.y, self.z = self._to_ecef()

    def _to_ecef(self):
        """
        Converts lat/lon to Earth-Centered Earth-Fixed (ECEF) coordinates.
        
        ECEF rotates with Earth — X points to prime meridian at equator,
        Z points to North Pole, Y completes the right-hand system.
        
        This is what your C slant_range() function expects as ground position.
        """
        lat_r = math.radians(self.lat)
        lon_r = math.radians(self.lon)

        x = self.EARTH_RADIUS * math.cos(lat_r) * math.cos(lon_r)
        y = self.EARTH_RADIUS * math.cos(lat_r) * math.sin(lon_r)
        z = self.EARTH_RADIUS * math.sin(lat_r)

        return x, y, z

    def summary(self):
        print(f"\n{'='*45}")
        print(f"  TARGET : {self.name}")
        print(f"{'='*45}")
        print(f"  Description : {self.description}")
        print(f"  Latitude    : {self.lat}°")
        print(f"  Longitude   : {self.lon}°")
        print(f"  ECEF X      : {self.x:.2f} km")
        print(f"  ECEF Y      : {self.y:.2f} km")
        print(f"  ECEF Z      : {self.z:.2f} km")
        print(f"{'='*45}")


if __name__ == "__main__":

    # The two targets for your Coverage Inequality Report
    okmok = Target(
        name        = "Okmok Volcano",
        lat         = 53.43,
        lon         = -168.13,
        description = "Alaska, USA — high latitude, excellent SAR revisit"
    )

    nyiragongo = Target(
        name        = "Nyiragongo Volcano",
        lat         = -1.52,
        lon         = 29.25,
        description = "DR Congo — equatorial, poor SAR revisit geometry"
    )

    okmok.summary()
    nyiragongo.summary()

    print("\nThese two targets are the core of the Coverage Inequality Report.")
    print("Same satellite. Same constellation. Completely different data reality.")