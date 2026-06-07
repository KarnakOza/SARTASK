from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tle_parser import parse_tle
from satellite import Satellite
from target import Target
from pass_finder import find_passes


def generate_pass_quality_report(satellite, target, passes, output_path):
    """
    Generates a professional PDF pass quality report.
    This is what a mission planner hands to their team
    before a SAR acquisition campaign.
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # --- Styles ---
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title",
        parent=styles["Normal"],
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0a1628"),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#4a5568"),
        alignment=TA_CENTER,
        spaceAfter=4
    )

    section_style = ParagraphStyle(
        "section",
        parent=styles["Normal"],
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0a1628"),
        spaceBefore=16,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "body",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#2d3748"),
        spaceAfter=4
    )

    # --- Build content ---
    story = []

    # Header
    story.append(Paragraph("SARTASK", title_style))
    story.append(Paragraph(
        "SAR Mission Tasking Engine — Pass Quality Report", subtitle_style))
    story.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style))
    story.append(Spacer(1, 0.5*cm))

    # Horizontal rule via a thin table
    story.append(Table(
        [[""]],
        colWidths=[17*cm],
        style=TableStyle([
            ("LINEBELOW", (0,0), (-1,-1), 1.5,
             colors.HexColor("#0a1628"))
        ])
    ))
    story.append(Spacer(1, 0.4*cm))

    # Mission parameters
    story.append(Paragraph("Mission Parameters", section_style))

    params_data = [
        ["Parameter", "Value"],
        ["Satellite",       satellite.name],
        ["Target",          target.name],
        ["Target Location", f"{target.lat}°N, {target.lon}°E"],
        ["Target Description", target.description],
        ["Orbital Altitude", f"{satellite.altitude():.1f} km"],
        ["Orbital Period",  f"{satellite.orbital_period():.2f} min"],
        ["Inclination",     f"{satellite.inclination}°"],
        ["Sun-Synchronous", str(satellite.is_sun_synchronous())],
        ["Analysis Window", "72 hours"],
        ["Total Passes",    str(len(passes))],
    ]

    params_table = Table(params_data, colWidths=[6*cm, 11*cm])
    params_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#0a1628")),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("BACKGROUND",  (0,1), (0,-1),  colors.HexColor("#edf2f7")),
        ("FONTNAME",    (0,1), (0,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",   (0,1), (0,-1),  colors.HexColor("#0a1628")),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#f7fafc")]),
        ("PADDING",     (0,0), (-1,-1), 6),
    ]))

    story.append(params_table)
    story.append(Spacer(1, 0.4*cm))

    # Pass quality table
    story.append(Paragraph("Ranked Pass Schedule", section_style))
    story.append(Paragraph(
        "Passes ranked by quality score. Score considers incidence angle "
        "optimality, elevation, and imaging duration. "
        "Optimal SAR incidence: 25°–50°.",
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    sorted_passes = sorted(passes, key=lambda x: x["score"], reverse=True)

    table_data = [[
        "Rank", "Start (UTC)", "Duration", "Max Elev.", "Score", "Recommendation"
    ]]

    for i, p in enumerate(sorted_passes):
        if p["score"] >= 45:
            rec = "OPTIMAL"
        elif p["score"] >= 30:
            rec = "GOOD"
        elif p["score"] >= 20:
            rec = "MARGINAL"
        else:
            rec = "POOR"

        table_data.append([
            str(i+1),
            p["start"].strftime("%Y-%m-%d %H:%M"),
            f"{p['duration_min']}m",
            f"{p['max_elevation']}°",
            f"{p['score']}/100",
            rec
        ])

    pass_table = Table(
        table_data,
        colWidths=[1.2*cm, 4.5*cm, 2.2*cm, 2.5*cm, 2.3*cm, 4.3*cm]
    )

    # Color rows by recommendation
    pass_style = [
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#0a1628")),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8.5),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("PADDING",     (0,0), (-1,-1), 5),
    ]

    for i, p in enumerate(sorted_passes, start=1):
        if p["score"] >= 45:
            bg = colors.HexColor("#c6f6d5")   # green
        elif p["score"] >= 30:
            bg = colors.HexColor("#fefcbf")   # yellow
        elif p["score"] >= 20:
            bg = colors.HexColor("#fed7aa")   # orange
        else:
            bg = colors.HexColor("#fed7d7")   # red
        pass_style.append(("BACKGROUND", (5,i), (5,i), bg))

    pass_table.setStyle(TableStyle(pass_style))
    story.append(pass_table)
    story.append(Spacer(1, 0.4*cm))

    # Coverage summary
    story.append(Paragraph("Coverage Summary", section_style))

    optimal = sum(1 for p in passes if p["score"] >= 45)
    good    = sum(1 for p in passes if 30 <= p["score"] < 45)
    poor    = sum(1 for p in passes if p["score"] < 30)
    best    = max(passes, key=lambda x: x["score"])

    summary_data = [
        ["Metric", "Value"],
        ["Total passes (72h)",      str(len(passes))],
        ["Optimal passes (≥45)",    str(optimal)],
        ["Good passes (30-44)",     str(good)],
        ["Poor passes (<30)",       str(poor)],
        ["Best pass time",
         best["start"].strftime("%Y-%m-%d %H:%M UTC")],
        ["Best pass score",         f"{best['score']}/100"],
        ["Avg pass duration",
         f"{sum(p['duration_min'] for p in passes)/len(passes):.1f} min"],
    ]

    summary_table = Table(summary_data, colWidths=[6*cm, 11*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#0a1628")),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("BACKGROUND",  (0,1), (0,-1),  colors.HexColor("#edf2f7")),
        ("FONTNAME",    (0,1), (0,-1),  "Helvetica-Bold"),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#f7fafc")]),
        ("PADDING",     (0,0), (-1,-1), 6),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.4*cm))

    # Footer
    story.append(Table(
        [[""]],
        colWidths=[17*cm],
        style=TableStyle([
            ("LINEABOVE", (0,0), (-1,-1), 0.5,
             colors.HexColor("#cbd5e0"))
        ])
    ))

    footer = ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=7.5,
        fontName="Helvetica",
        textColor=colors.HexColor("#a0aec0"),
        alignment=TA_CENTER,
        spaceBefore=4
    )
    story.append(Paragraph(
        "SARTASK — SAR Mission Tasking Engine | "
        "Orbital propagation via SGP4 | "
        "SAR geometry via custom C engine | "
        "github.com/yourusername/SARTASK",
        footer
    ))

    doc.build(story)
    print(f"\n  Report saved → {output_path}")


if __name__ == "__main__":

    os.makedirs("outputs", exist_ok=True)

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

    okmok = Target(
        "Okmok Volcano", 53.43, -168.13,
        "Alaska, USA — high latitude volcanic monitoring target"
    )

    print(f"Finding passes...")
    passes = find_passes(sat, okmok, hours=72)

    print(f"Generating PDF report...")
    generate_pass_quality_report(
        sat, okmok, passes,
        "outputs/pass_quality_okmok.pdf"
    )
