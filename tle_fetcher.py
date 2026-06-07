import urllib.request
import os
from datetime import datetime, timezone


CELESTRAK_GROUPS = {
    "resource": "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=TLE",
}

INDIVIDUAL_SATELLITES = {
    "SENTINEL-1C": "https://celestrak.org/NORAD/elements/gp.php?CATNR=62261&FORMAT=TLE",
    "SENTINEL-1D": "https://celestrak.org/NORAD/elements/gp.php?CATNR=66315&FORMAT=TLE",
    "NISAR"      : "https://celestrak.org/NORAD/elements/gp.php?CATNR=62912&FORMAT=TLE",
}

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
    """
    Fetches TLEs from Celestrak with silent fallback to local file.
    On Streamlit Cloud, outbound HTTP is blocked — falls back immediately
    to data/tle/satellites.txt which is committed to the repo.
    """
    os.makedirs(cache_dir, exist_ok=True)
    group_cache = os.path.join(cache_dir, "earth_obs_group.tle")

    # Check cache freshness
    use_cache = False
    if os.path.exists(group_cache):
        age_hours = (
            datetime.now(timezone.utc).timestamp() -
            os.path.getmtime(group_cache)
        ) / 3600
        if age_hours < 6:
            use_cache = True

    if not use_cache:
        group_content = ""
        for group_name, url in CELESTRAK_GROUPS.items():
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "SARTASK/1.0"}
                )
                # Short timeout — don't hang if network is blocked
                with urllib.request.urlopen(req, timeout=5) as resp:
                    group_content += resp.read().decode("utf-8")
            except Exception:
                pass  # Silent fail — local fallback handles it

        # Only save cache if we got real TLE data
        if group_content and "1 " in group_content and "removed" not in group_content[:100]:
            with open(group_cache, "w") as f:
                f.write(group_content)
        else:
            # Network blocked or bad response — use local file
            return _load_all_local()

    with open(group_cache, "r") as f:
        content = f.read()

    results = _extract_satellites(content)
    individual = _fetch_individual(cache_dir)
    results.update(individual)

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
    results = {}
    for name, url in INDIVIDUAL_SATELLITES.items():
        safe       = name.replace(" ", "_").replace("-", "_")
        cache_path = os.path.join(cache_dir, f"{safe}.tle")

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
                    continue

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "SARTASK/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
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
        except Exception:
            pass  # Silent fail

    return results


def _load_all_local():
    results = {}
    for name in SAR_SATELLITE_NAMES:
        data = _load_single_local(name)
        if data:
            results[name] = data
    return results


def _load_single_local(satellite_name):
    # Try multiple possible paths — works both locally and on Streamlit Cloud
    possible_paths = [
        "data/tle/satellites.txt",
        os.path.join(os.path.dirname(__file__), "data/tle/satellites.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/tle/satellites.txt"),
    ]

    for path in possible_paths:
        try:
            if not os.path.exists(path):
                continue
            from tle_parser import parse_tle
            tle_data = parse_tle(path)
            if satellite_name in tle_data:
                el = tle_data[satellite_name]
                return {
                    "name" : satellite_name,
                    "line1": el["line1"],
                    "line2": el["line2"],
                    "source": "local-fallback"
                }
        except Exception:
            continue
    return None


if __name__ == "__main__":
    satellites = fetch_all_sar_satellites()
    print(f"\n  {len(satellites)}/{len(SAR_SATELLITE_NAMES)} satellites ready\n")
    for name, data in satellites.items():
        print(f"  {name}: source={data['source']}")
        print(f"    line1={data['line1'][:60]}")
