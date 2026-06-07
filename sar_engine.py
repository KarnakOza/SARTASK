import ctypes
import os
import sys
import subprocess
import platform

def _load_library():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if platform.system() == "Windows":
        # Local Windows dev — use the pre-compiled DLL
        dll_path = os.path.join(base_dir, "sar_engine.dll")
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"sar_engine.dll not found at {dll_path}")
        return ctypes.CDLL(dll_path)

    else:
        # Linux (Streamlit Cloud) — compile .so if not already built
        so_path = os.path.join(base_dir, "sar_engine.so")

        if not os.path.exists(so_path):
            build_script = os.path.join(base_dir, "build_sar_engine.sh")
            if not os.path.exists(build_script):
                raise FileNotFoundError(f"build_sar_engine.sh not found at {build_script}")
            print("sar_engine.so not found — compiling from source...")
            result = subprocess.run(
                ["bash", build_script],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to compile sar_engine.so:\n{result.stderr}"
                )
            print(result.stdout)

        return ctypes.CDLL(so_path)


lib = _load_library()

# ── Function signatures ────────────────────────────────────────────────────────

lib.orbital_velocity.argtypes = [ctypes.c_double]
lib.orbital_velocity.restype  = ctypes.c_double

lib.orbital_period.argtypes = [ctypes.c_double]
lib.orbital_period.restype  = ctypes.c_double

lib.doppler_centroid.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
lib.doppler_centroid.restype  = ctypes.c_double

lib.slant_range.argtypes = [ctypes.c_double] * 6
lib.slant_range.restype  = ctypes.c_double

# ── Public API ─────────────────────────────────────────────────────────────────

def get_orbital_velocity(altitude_km):
    return lib.orbital_velocity(altitude_km)

def get_orbital_period(altitude_km):
    return lib.orbital_period(altitude_km)

def get_doppler(velocity_kms, wavelength_m, squint_angle_rad):
    return lib.doppler_centroid(velocity_kms, wavelength_m, squint_angle_rad)

def get_slant_range(sat_x, sat_y, sat_z, gnd_x, gnd_y, gnd_z):
    return lib.slant_range(sat_x, sat_y, sat_z, gnd_x, gnd_y, gnd_z)


# ── Quick self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    altitude   = 693.0
    wavelength = 0.056
    squint     = 0.2

    velocity = get_orbital_velocity(altitude)
    period   = get_orbital_period(altitude)
    doppler  = get_doppler(velocity, wavelength, squint)
    slant    = get_slant_range(7071.0, 0.0, 0.0, 6378.0, 0.0, 0.0)

    print(f"\n{'='*45}")
    print(f"  SAR ENGINE — C library called from Python")
    print(f"{'='*45}")
    print(f"  Platform         : {platform.system()}")
    print(f"  Altitude         : {altitude} km")
    print(f"  Orbital Velocity : {velocity:.4f} km/s")
    print(f"  Orbital Period   : {period:.2f} s ({period/60:.2f} min)")
    print(f"  Doppler Centroid : {doppler:.2f} Hz")
    print(f"  Slant Range      : {slant:.2f} km")
    print(f"{'='*45}")
