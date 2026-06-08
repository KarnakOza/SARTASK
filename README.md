<div align="center">

# SARTASK
### SAR Mission Tasking Engine

**An open mission planning tool that finds the optimal SAR imaging window for any target on Earth.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-sartask.streamlit.app-00ff41?style=for-the-badge&logo=streamlit)](https://sartask.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-00aa2b?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-0088aa?style=for-the-badge)](LICENSE)

</div>

---

## The Problem

When you're doing SAR-based monitoring — volcanoes, floods, subsidence, deforestation — you need to know *which* satellite pass gives you the best image geometry for your target. Not just when a satellite passes overhead, but which pass gives you the right incidence angle, the right Doppler centroid, the right imaging geometry.

Current tools either cost $50,000/year (AGI STK) or don't exist as open software.

**SARTASK solves this.**

---

## The Key Finding

Running SARTASK on two volcanic monitoring targets with the same satellite (Sentinel-1A) over 72 hours:

| Target | Location | Passes (72hrs) | Best Score |
|--------|----------|---------------|------------|
| Okmok Volcano | 53.4°N, Alaska | **19 passes** | 93.6/100 |
| Nyiragongo Volcano | -1.5°, DR Congo | **10 passes** | 75.4/100 |

> Same satellite. Same time window. **High latitude gets nearly 2× the imaging opportunity.**

This is the orbital geometry reality that affects every SAR monitoring mission. When Sentinel-1B failed in August 2021 and the 6-day repeat became 12 days, this inequality doubled. SARTASK quantifies it.

---

## What It Does

Given a target location and a SAR satellite, SARTASK:

1. Fetches live TLE orbital data from Celestrak
2. Propagates the orbit forward 72 hours using SGP4
3. Computes pass geometry using a custom C physics engine
4. Scores each pass 0–100 based on incidence angle, elevation, and duration
5. Outputs a ranked pass schedule and downloadable PDF mission report

**It answers the question every EO mission planner asks:**
> *"Which pass in the next 72 hours gives me the best SAR image of this target?"*

---

## Live Demo

**[sartask.streamlit.app](https://sartask.streamlit.app/)**

Select a satellite, enter any target coordinates (or choose a preset), click Execute Tasking. Get a ranked pass schedule, interactive ground track map, and downloadable PDF report in under 30 seconds.

---

## Architecture

```
Live TLE (Celestrak)
        │
        ▼
┌───────────────────┐
│   TLE Parser      │  Parses NORAD two-line element sets
│   tle_parser.py   │  Fixed-width character extraction
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  SGP4 Propagator  │  python-sgp4 library
│  propagator.py    │  ECI → ECEF → lat/lon via GMST rotation
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────┐
│         C Physics Engine              │
│  sar_engine/  →  sar_engine.dll/.so   │
│                                       │
│  vec3.c          3D vector library    │
│  orbit.c         Orbital velocity     │
│  eci_position.c  ECI from 6 elements  │
│  eci_to_ecef.c   Coordinate transform │
│  geometry.c      Slant range geometry │
│  doppler.c       Doppler centroid     │
│  telemetry.c     Full pass telemetry  │
└────────┬──────────────────────────────┘
         │
         ▼
┌───────────────────┐
│   Pass Finder     │  Elevation angle detection
│   pass_finder.py  │  Incidence angle computation
│                   │  Pass quality scoring 0-100
└────────┬──────────┘
         │
         ▼
┌─────────────────────────────┐
│        Reports              │
│                             │
│  Pass Quality PDF           │  Ranked table, color-coded
│  Coverage Inequality Chart  │  High vs equatorial targets
│  Streamlit Dashboard        │  Interactive ops-room UI
└─────────────────────────────┘
```

---

## Pass Quality Score

Each pass is scored 0–100:

| Component | Weight | Criteria |
|-----------|--------|----------|
| Incidence angle | 50 pts | Optimal 25–50°, peak at 37.5° |
| Max elevation | 30 pts | Higher = longer imaging window |
| Pass duration | 20 pts | Longer = more imaging opportunity |

Scores are classified as OPTIMAL (≥45), GOOD (30–44), MARGINAL (20–29), or POOR (<20).

---

## Supported Satellites

All TLEs fetched live from Celestrak:

| Satellite | Agency | Band | Altitude |
|-----------|--------|------|----------|
| Sentinel-1A | ESA | C | 693 km |
| Sentinel-1C | ESA | C | 693 km |
| Sentinel-1D | ESA | C | 693 km |
| TerraSAR-X | DLR | X | 514 km |
| COSMO-SkyMed 1 | ASI | X | 619 km |
| RADARSAT-2 | CSA | C | 798 km |
| NISAR | NASA/ISRO | L+S | 747 km |

---

## Installation

```bash
git clone https://github.com/KarnakOza/SARTASK.git
cd SARTASK
pip install -r requirements.txt
```

**Compile the C physics engine (Windows/MinGW):**
```bash
gcc -shared -o sar_engine.dll -fPIC \
    sar_engine/vec3.c sar_engine/orbit.c \
    sar_engine/eci_position.c sar_engine/eci_to_ecef.c \
    sar_engine/geometry.c sar_engine/doppler.c \
    sar_engine/sar_range.c sar_engine/telemetry.c -lm
```

**Run locally:**
```bash
streamlit run sartask_app.py
```

---

## Requirements

```
streamlit
sgp4
folium
streamlit-folium
pandas
reportlab
numpy
matplotlib
Pillow
```

---

## C Physics Engine

The SAR geometry calculations run in a custom C library compiled to a shared object (`.dll` on Windows, `.so` on Linux). Python calls it via `ctypes` — the same architecture used in production aerospace software.

The engine computes:

```c
// Satellite position in ECI frame
Vec3 satellite_position_eci(double a, double e, double i,
                             double raan, double omega, double nu);

// Slant range between satellite and ground point
double slant_range(double xs, double ys, double zs,
                   double xg, double yg, double zg);

// Doppler centroid
double doppler_centroid(double velocity, double wavelength, double angle);

// Orbital velocity
double orbital_velocity(double altitude);
```

Validated against Vallado AIAA-2006-6753 reference vectors. Position errors < 10m for fresh TLEs.

---

## Validation

| Parameter | SARTASK | Published Spec | Error |
|-----------|---------|---------------|-------|
| Sentinel-1A altitude | 696.6 km | 693 km | 3.6 km |
| Orbital period | 98.68 min | 98.6 min | 0.08 min |
| Orbital velocity | 7.508 km/s | 7.51 km/s | 0.002 km/s |
| SSO classification | True | True | — |

Small altitude error is due to TLE epoch offset — fresh TLEs from Celestrak reduce this to < 1 km.

---

## Project Structure

```
SARTASK/
├── sartask_app.py          # Streamlit dashboard
├── tle_parser.py           # TLE file parser
├── satellite.py            # Satellite class (orbital mechanics)
├── target.py               # Target class (ECEF coordinates)
├── propagator.py           # SGP4 propagation + ECI→ECEF
├── pass_finder.py          # Pass detection + quality scoring
├── tle_fetcher.py          # Live TLE fetch from Celestrak
├── sar_engine/             # C physics engine source
│   ├── vec3.c/h            # 3D vector library
│   ├── orbit.c             # Orbital velocity + period
│   ├── eci_position.c      # Satellite position in ECI
│   ├── eci_to_ecef.c       # Coordinate transformation
│   ├── geometry.c          # Slant range geometry
│   ├── doppler.c           # Doppler centroid
│   ├── telemetry.c/h       # Full pass telemetry struct
│   └── constants.h         # Physical constants (μ, R⊕, c)
├── reports/
│   └── pass_quality.py     # PDF report generator
├── data/
│   └── tle/
│       └── satellites.txt  # Fallback TLE data
└── outputs/                # Generated PDFs
```

---

## Coverage Inequality — The Core Finding

```
SENTINEL-1A · 72 HOUR ANALYSIS WINDOW
═══════════════════════════════════════════════════════
OKMOK VOLCANO    [53.4°N — ALASKA]    → 19 passes
NYIRAGONGO VOL   [-1.5°  — DR CONGO] → 10 passes

SAME PLATFORM. SAME WINDOW.
HIGH LATITUDE = 1.9× MORE IMAGING OPPORTUNITIES.

This mirrors the Sentinel-1B failure impact (2021–2024):
high-latitude users lost less relative coverage than
equatorial users when the 6-day repeat became 12 days.
═══════════════════════════════════════════════════════
```

---

## Planned

- Coverage Inequality Report (side-by-side multi-target comparison)
- Constellation Gap Analysis (Sentinel-1B failure scenario recreation)
- Mission Design Summary PDF (monitoring need → satellite recommendation)
- FastAPI backend for multi-user deployment
- Real SAR file upload and backscatter analysis
- AIS integration for maritime target correlation

---

## Background

Built by an aerospace engineering graduate with a background in SAR geometry, InSAR analysis, and orbital mechanics. This project grew from a question I couldn't stop thinking about after running Okmok InSAR analysis: *why did the data just appear, consistent and reliable — and what happens to targets where it doesn't?*

The answer is orbital geometry. SARTASK makes that answer quantitative.

---

## References

- Vallado, D.A. (2006). *Revisiting Spacetrack Report #3*. AIAA 2006-6753
- ESA Sentinel-1 Mission Guide
- Celestrak NORAD Two-Line Element Sets
- Hooper et al. (2012). Recent advances in SAR interferometry

---

<div align="center">

**[Live Demo](https://sartask.streamlit.app/) · [GitHub](https://github.com/KarnakOza/SARTASK)**

*Orbital propagation via SGP4 · SAR geometry via custom C engine · Live TLE data from Celestrak*

</div>
