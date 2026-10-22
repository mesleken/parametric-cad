"""Engineering Datasheet (PDF) generator using ReportLab."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

from pcad.domain.materials import Material
from pcad.domain.template import CheckResult, MarginStatus, PhysicsResult

def generate_datasheet_pdf(
    output_pdf_path: Path,
    template_name: str,
    template_version: str,
    params: Dict[str, Any],
    material: Material,
    physics: PhysicsResult,
    checks: List[CheckResult],
    model_hash: str,
    preview_png_path: Optional[Path] = None
) -> Path:
    """Generates a professional single-page PDF engineering datasheet."""
    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568")
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4
    )
    cell_style = ParagraphStyle("CellText", parent=styles["Normal"], fontSize=8, leading=10)
    bold_cell_style = ParagraphStyle("BoldCellText", parent=styles["Normal"], fontSize=8, leading=10, fontName="Helvetica-Bold")
    
    story = []
    
    # 1. Header
    story.append(Paragraph(f"<b>PCAD ENGINEERING DATASHEET</b> — {template_name}", title_style))
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    hash_short = model_hash[:12] if model_hash else "N/A"
    story.append(Paragraph(f"Date: {date_str} | Template Version: {template_version} | Model Hash: {hash_short}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8, spaceBefore=4))
    
    # 2. Main Body: Left (Image), Right (Physical Properties & Material)
    top_cols = []
    
    # Preview Image
    if preview_png_path and Path(preview_png_path).exists():
        img = Image(str(preview_png_path), width=240, height=180)
    else:
        img = Paragraph("<i>[No 3D Preview Available]</i>", cell_style)
        
    # Physical Properties Table
    phys_data = [
        [Paragraph("<b>Property</b>", bold_cell_style), Paragraph("<b>Value</b>", bold_cell_style)],
        [Paragraph("Material", cell_style), Paragraph(material.name, cell_style)],
        [Paragraph("Density", cell_style), Paragraph(f"{material.density_g_cm3:.2f} g/cm³", cell_style)],
        [Paragraph("Mass", cell_style), Paragraph(f"<b>{physics.mass_g:.1f} g</b> ({physics.mass_g/1000.0:.3f} kg)", cell_style)],
        [Paragraph("Volume", cell_style), Paragraph(f"{physics.volume_mm3:.1f} mm³", cell_style)],
        [Paragraph("Surface Area", cell_style), Paragraph(f"{physics.surface_area_mm2:.1f} mm²", cell_style)],
        [Paragraph("Center of Gravity (X, Y, Z)", cell_style), Paragraph(f"({physics.cog_mm[0]}, {physics.cog_mm[1]}, {physics.cog_mm[2]}) mm", cell_style)],
        [Paragraph("Inertia (Ixx, Iyy, Izz)", cell_style), Paragraph(f"({physics.inertia_g_mm2[0]:.0f}, {physics.inertia_g_mm2[1]:.0f}, {physics.inertia_g_mm2[2]:.0f}) g·mm²", cell_style)],
    ]
    t_phys = Table(phys_data, colWidths=[110, 160])
    t_phys.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    
    top_layout_table = Table([[img, t_phys]], colWidths=[245, 275])
    top_layout_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(top_layout_table)
    
    # 3. Parameters Table
    story.append(Paragraph("Design Parameters", section_style))
    param_rows = [[Paragraph("<b>Parameter</b>", bold_cell_style), Paragraph("<b>Value</b>", bold_cell_style)]]
    for k, v in sorted(params.items()):
        val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
        param_rows.append([Paragraph(str(k), cell_style), Paragraph(val_str, cell_style)])
    
    # Split into 2 columns of params for compact look
    half = (len(param_rows) + 1) // 2
    col1 = param_rows[:half]
    col2 = [param_rows[0]] + param_rows[half:]
    t_p1 = Table(col1, colWidths=[150, 100])
    t_p1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    t_p2 = Table(col2, colWidths=[150, 100])
    t_p2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    params_layout = Table([[t_p1, t_p2]], colWidths=[260, 260])
    params_layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(params_layout)
    
    # 4. Engineering Verification & Margins of Safety
    story.append(Paragraph("Engineering Verification & Margins of Safety", section_style))
    chk_rows = [[
        Paragraph("<b>Check / Mode</b>", bold_cell_style),
        Paragraph("<b>Applied</b>", bold_cell_style),
        Paragraph("<b>Allowable</b>", bold_cell_style),
        Paragraph("<b>FoS</b>", bold_cell_style),
        Paragraph("<b>Margin (MS)</b>", bold_cell_style),
        Paragraph("<b>Status</b>", bold_cell_style),
    ]]
    for chk in checks:
        ms_str = f"+{chk.margin_of_safety:.2f}" if chk.margin_of_safety > 0 and chk.margin_of_safety < 900 else (f"{chk.margin_of_safety:.2f}" if chk.margin_of_safety < 900 else "+Inf")
        if chk.status == MarginStatus.POSITIVE:
            stat_color = "#38A169" # Green
            stat_text = "POSITIVE"
        elif chk.status == MarginStatus.LOW:
            stat_color = "#D69E2E" # Yellow
            stat_text = "LOW MARGIN"
        else:
            stat_color = "#E53E3E" # Red
            stat_text = "NEGATIVE"
            
        chk_rows.append([
            Paragraph(f"<b>{chk.name}</b><br/><font size=6 color='#718096'>{chk.rule_ref}</font>", cell_style),
            Paragraph(f"{chk.applied} {chk.unit}", cell_style),
            Paragraph(f"{chk.allowable} {chk.unit}", cell_style),
            Paragraph(f"{chk.fos:.1f}", cell_style),
            Paragraph(f"<b>{ms_str}</b>", cell_style),
            Paragraph(f"<b><font color='{stat_color}'>{stat_text}</font></b>", cell_style)
        ])
        
    t_chk = Table(chk_rows, colWidths=[150, 75, 75, 45, 80, 95])
    t_chk.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_chk)
    
    # 5. Disclaimer Footer
    story.append(Spacer(1, 10))
    disclaimer = (
        "<b>DISCLAIMER:</b> PRELIMINARY SIZING AND GEOMETRIC DESIGN ONLY — NOT A CERTIFICATION RECORD. "
        "Calculations are based on simplified analytical handbook methods and do not replace detailed FEA, "
        "experimental structural qualification, or formal airworthiness certification. Independent engineering check required."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle("Disc", parent=styles["Normal"], fontSize=6.5, leading=8.5, textColor=colors.HexColor("#718096"))))
    
    doc.build(story)
    return output_pdf_path
