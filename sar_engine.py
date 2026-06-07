import ctypes
import os

#Loading the compiled C library
dll_path = os.path.join(os.path.dirname(__file__), "..", "sar_engine.dll")
lib = ctypes.CDLL(dll_path)

lib.orbital_velocity.argtypes = [ctypes.c_double]
lib.orbital_velocity.restype = ctypes.c_double

lib.orbital_period.argtypes = [ctypes.c_double]
lib.orbital_period.restype = ctypes.c_double

lib.doppler_centroid.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
lib.doppler_centroid.restype = ctypes.c_double

lib.slant_range.argtypes = [ctypes.c_double] * 6
lib.slant_range.restype = ctypes.c_double

def get_orbital_velocity(altitude_km):
    return lib.orbital_velocity(altitude_km)

def get_orbital_period(altitude_km):
    return lib.orbital_period(altitude_km)

def get_doppler(velocity_kms, wavelength_m, squint_angle_rad):
    return lib.doppler_centroid(velocity_kms, wavelength_m, squint_angle_rad)

def get_slant_range(sat_x, sat_y, sat_z, gnd_x, gnd_y, gnd_z):
    return lib.slant_range(sat_x, sat_y, sat_z, gnd_x, gnd_y, gnd_z)

#Testing it directly?!

if __name__ == "__main__":
    
    altitude = 693.0          # Sentinel-1 altitude in km
    wavelength = 0.056        # C-band SAR wavelength in meters
    squint = 0.2              # squint angle in radians

    velocity = get_orbital_velocity(altitude)
    period   = get_orbital_period(altitude)
    doppler  = get_doppler(velocity, wavelength, squint)

    # Sentinel-1A position (simplified) and ground point
    slant = get_slant_range(7071.0, 0.0, 0.0, 6378.0, 0.0, 0.0)

    print(f"\n{'='*45}")
    print(f"  SAR ENGINE — C library called from Python")
    print(f"{'='*45}")
    print(f"  Altitude         : {altitude} km")
    print(f"  Orbital Velocity : {velocity:.4f} km/s")
    print(f"  Orbital Period   : {period:.2f} seconds ({period/60:.2f} min)")
    print(f"  Doppler Centroid : {doppler:.2f} Hz")
    print(f"  Slant Range      : {slant:.2f} km")
    print(f"{'='*45}")