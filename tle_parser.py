def parse_tle(filepath):

    satellites = {}

    with open(filepath, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()

        inclination  = float(line2[8:16])
        raan         = float(line2[17:25])
        eccentricity = float("0." + line2[26:33])
        mean_motion  = float(line2[52:63])  

        satellites[name] = {
            "line1": line1,
            "line2": line2,
            "inclination": inclination,
            "raan": raan,
            "eccentricity": eccentricity,
            "mean_motion": mean_motion
        }

        i += 3 

    return satellites

if __name__ == "__main__":
    data = parse_tle("data/tle/sentinel1.txt")

    for sat_name, elements in data.items():
        print(f"\n---{sat_name}---")
        print(f" Inclination : {elements['inclination']}°")
        print(f" RAAN        : {elements['raan']}°   ")
        print(f" Eccentricity: {elements['eccentricity']}")
        print(f" Mean Motion : {elements['mean_motion']}   rev/day")