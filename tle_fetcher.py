import urllib.request
import os
from datetime import datetime, timezone


# Celestrak GROUP URLs
CELESTRAK_GROUPS = {
    "resource": "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=TLE",
}

# Individual CATNR fetches for newer satellites not in group files
INDIVIDUAL_SATELLITES = {
    "SENTINEL-1C": "https://celestrak.org/NORAD/elements/gp.php?CATNR=62261&FORMAT=TLE",
    "SENTINEL-1D": "https://celestrak.org/NORAD/elements/gp.php?CATNR=66315&FORMAT=TLE",
    "NISAR"      : "https://celestrak.org/NORAD/elements/gp.php?CATNR=62912&FORMAT=TLE",
}

# All satellites we want
SAR_SATELLITE_NAMES = [
    "SENTINEL-1A",
    "SENTINEL-1C",
    "SENTINEL-1D",
    "TERRASAR-X",
    "COSMO-SKYMED 1",
    "RADARSAT-2",
    "NISAR",
]


def fetch_all_sar_satellites(cache_dir="data/tle/cache"):
    os.makedirs(cache_dir, exist_ok=True)
    group_cache = os.path.join(cache_dir, "earth_obs_group.tle")

    use_cache = False
    if os.path.exists(group_cache):
        age_hours = (
            datetime.now(timezone.utc).timestamp() -
            os.path.getmtime(group_cache)
        ) / 3600
        if age_hours < 6:
            print(f"  Using cached group TLE ({age_hours:.1f}h old)")
            use_cache = True

    if not use_cache:
        print("  Fetching resource group from Celestrak...")
        group_content = ""
        for group_name, url in CELESTRAK_GROUPS.items():
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "SARTASK/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    group_content += resp.read().decode("utf-8")
                print(f"  ✓ Fetched group: {group_name}")
            except Exception as e:
                print(f"  ✗ Failed group {group_name}: {e}")

        if group_content:
            with open(group_cache, "w") as f:
                f.write(group_content)
        else:
            print("  All fetches failed — using local fallback")
            return _load_all_local()

    with open(group_cache, "r") as f:
        content = f.read()

    # Extract from group file
    results = _extract_satellites(content)

    # Fetch newer satellites individually
    individual = _fetch_individual(cache_dir)
    results.update(individual)

    # Fill remaining with local fallback
    for name in SAR_SATELLITE_NAMES:
        if name not in results:
            fallback = _load_single_local(name)
            if fallback:
                results[name] = fallback

    return results


def _extract_satellites(tle_content):
    lines   = [l.strip() for l in tle_content.splitlines() if l.strip()]
    results = {}

    i = 0
    while i < len(lines) - 2:
        line = lines[i]
        if not line.startswith("1 ") and not line.startswith("2 "):
            name  = line.strip()
            line1 = lines[i+1] if i+1 < len(lines) else ""
            line2 = lines[i+2] if i+2 < len(lines) else ""

            if line1.startswith("1 ") and line2.startswith("2 "):
                for wanted in SAR_SATELLITE_NAMES:
                    if wanted.upper() in name.upper():
                        results[wanted] = {
                            "name"  : wanted,
                            "line1" : line1,
                            "line2" : line2,
                            "source": "celestrak-live"
                        }
                        break
                i += 3
                continue
        i += 1

    return results


def _fetch_individual(cache_dir="data/tle/cache"):
    """Fetch newer satellites not in group files by CATNR."""
    results = {}
    for name, url in INDIVIDUAL_SATELLITES.items():
        safe    = name.replace(" ", "_").replace("-", "_")
        cache_path = os.path.join(cache_dir, f"{safe}.tle")

        # Check cache freshness
        if os.path.exists(cache_path):
            age_hours = (
                datetime.now(timezone.utc).timestamp() -
                os.path.getmtime(cache_path)
            ) / 3600
            if age_hours < 6:
                with open(cache_path, "r") as f:
                    lines = [l.strip() for l in f.readlines()
                             if l.strip() and not l.startswith("#")]
                if len(lines) >= 2:
                    results[name] = {
                        "name"  : name,
                        "line1" : lines[-2],
                        "line2" : lines[-1],
                        "source": "cache"
                    }
                    print(f"  Using cached TLE for {name}")
                    continue

        # Fetch fresh
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "SARTASK/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8").strip()

            lines = [l.strip() for l in content.splitlines() if l.strip()]
            line1 = next((l for l in lines if l.startswith("1 ")), None)
            line2 = next((l for l in lines if l.startswith("2 ")), None)

            if line1 and line2 and "removed" not in line1.lower():
                with open(cache_path, "w") as f:
                    f.write(f"{name}\n{line1}\n{line2}\n")
                results[name] = {
                    "name"  : name,
                    "line1" : line1,
                    "line2" : line2,
                    "source": "celestrak-live"
                }
                print(f"  ✓ Fetched individual: {name}")
            else:
                print(f"  ✗ CATNR returned no valid TLE: {name}")

        except Exception as e:
            print(f"  ✗ {name}: {e}")

    return results


def _load_all_local():
    results = {}
    for name in SAR_SATELLITE_NAMES:
        data = _load_single_local(name)
        if data:
            results[name] = data
    return results


def _load_single_local(satellite_name):
    try:
        from tle_parser import parse_tle
        tle_data = parse_tle("data/tle/satellites.txt")
        if satellite_name in tle_data:
            el = tle_data[satellite_name]
            return {
                "name" : satellite_name,
                "line1": el["line1"],
                "line2": el["line2"],
                "source": "local-fallback"
            }
    except Exception:
        pass
    return None


if __name__ == "__main__":
    satellites = fetch_all_sar_satellites()
    print(f"\n  {len(satellites)}/{len(SAR_SATELLITE_NAMES)} satellites ready\n")
    for name, data in satellites.items():
        print(f"  {name}: source={data['source']}")
        print(f"    line1={data['line1'][:60]}")