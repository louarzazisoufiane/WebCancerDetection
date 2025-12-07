"""PDF report generation helpers (professional layout).

Generates a PDF with header, model summary, top features and a SHAP bar chart image.
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import plotly.graph_objects as go
import plotly.io as pio


def _fig_to_png_bytes(fig: go.Figure) -> bytes:
    """Render Plotly figure to PNG using kaleido via plotly.io.to_image"""
    return pio.to_image(fig, format='png', width=1000, height=600)


def generate_professional_pdf(title: str, explanation: Dict[str, Any], fig: Optional[go.Figure] = None, meta: Dict[str, str] = None) -> bytes:
    """Create a polished PDF report and return bytes.

    - title: report title
    - explanation: result from explain_model_prediction
    - fig: optional Plotly figure (bar chart)
    - meta: additional metadata (model, probability, date, user)
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont('Helvetica-Bold', 18)
    c.drawString(48, height - 60, title)
    c.setFont('Helvetica', 10)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    c.drawRightString(width - 48, height - 60, now)

    # Meta block
    y = height - 90
    if meta:
        c.setFont('Helvetica-Bold', 11)
        c.drawString(48, y, 'Contexte:')
        y -= 14
        c.setFont('Helvetica', 10)
        for k, v in meta.items():
            c.drawString(56, y, f"{k}: {v}")
            y -= 12
        y -= 8

    # Top features
    c.setFont('Helvetica-Bold', 12)
    c.drawString(48, y, 'Top Features (contributions SHAP)')
    y -= 16
    c.setFont('Helvetica', 10)
    top = explanation.get('top_features', []) if explanation else []
    for item in top:
        txt = f"- {item.get('feature')}: {item.get('shap_value'):.4f}"
        c.drawString(56, y, txt)
        y -= 12
        if y < 160:
            c.showPage()
            y = height - 60

    # Add explanatory text
    if explanation and explanation.get('base_value') is not None:
        y -= 8
        c.setFont('Helvetica-Bold', 11)
        c.drawString(48, y, 'Interprétation :')
        y -= 14
        c.setFont('Helvetica', 10)
        c.drawString(56, y, f"Base value: {explanation.get('base_value'):.4f}")
        y -= 14

    # Insert figure if provided
    if fig is not None:
        try:
            img_bytes = _fig_to_png_bytes(fig)
            img = ImageReader(io.BytesIO(img_bytes))
            # Leave margin and draw image
            iw = width - 96
            ih = iw * 0.5
            if y - ih < 40:
                c.showPage()
                y = height - 60
            c.drawImage(img, 48, y - ih, width=iw, height=ih, preserveAspectRatio=True, mask='auto')
            y = y - ih - 20
        except Exception:
            # ignore image errors
            pass

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
