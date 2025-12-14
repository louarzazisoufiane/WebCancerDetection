"""PDF report generation helpers (professional layout).

Generates a polished PDF with branding, patient summary, and dual SHAP/LIME analysis.
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import plotly.graph_objects as go
import plotly.io as pio

# --- Constants ---
PRIMARY_COLOR = colors.HexColor("#2563eb")  # Blue-600
SECONDARY_COLOR = colors.HexColor("#1e40af") # Blue-800
ACCENT_COLOR = colors.HexColor("#3b82f6")   # Blue-500
DANGER_COLOR = colors.HexColor("#ef4444")
SUCCESS_COLOR = colors.HexColor("#10b981")
NEUTRAL_LIGHT = colors.HexColor("#f3f4f6")

def _fig_to_png_bytes(fig: go.Figure) -> bytes:
    """Render Plotly figure to PNG using kaleido via plotly.io.to_image"""
    # Increase scale for better quality
    return pio.to_image(fig, format='png', width=1000, height=500, scale=2)

def generate_professional_pdf(
    title: str, 
    shap_explanation: Dict[str, Any], 
    lime_explanation: Optional[Dict[str, Any]] = None,
    shap_fig: Optional[go.Figure] = None, 
    lime_fig: Optional[go.Figure] = None,
    meta: Dict[str, str] = None,
    input_data: Dict[str, Any] = None
) -> bytes:
    """Create a polished PDF report using ReportLab Platypus."""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    story = []

    # --- Styles ---
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.white,
        backColor=SECONDARY_COLOR,
        borderPadding=(8, 8, 8, 8),
        borderRadius=4,
        spaceBefore=20,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='NormalSmall',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#4b5563")
    ))

    # --- Header ---
    # Branding
    story.append(Paragraph("SkinCheck", styles['MainTitle']))
    story.append(Paragraph("Rapport d'Analyse Dermatologique Assistée par IA", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Meta / Creation Date
    date_str = datetime.now().strftime('%d/%m/%Y à %H:%M')
    story.append(Paragraph(f"Généré le {date_str}", styles['NormalSmall']))
    story.append(Spacer(1, 20))

    # --- Patient / Input Summary ---
    if input_data:
        story.append(Paragraph("Données Patient & Facteurs de Risque", styles['SectionHeader']))
        
        # Prepare table data
        # Convert dict to list of lists for Table
        table_data = []
        row = []
        col_count = 0
        
        for k, v in input_data.items():
            # Clean keys
            label = k.replace('_', ' ').title()
            # Clean values
            val_str = str(v)
            if isinstance(v, float):
                val_str = f"{v:.1f}"
                
            # Use Paragraph to properly render bold text
            row.append(Paragraph(f"<b>{label}:</b>", styles['Normal']))
            row.append(Paragraph(val_str, styles['Normal']))
            col_count += 1
            
            if col_count == 3: # 3 items (key-val pairs) per row -> actually 6 cols
                table_data.append(row)
                row = []
                col_count = 0
                
        if row: # remaining
            # fill empty
            while len(row) < 6:
                row.append(Paragraph("", styles['Normal']))
            table_data.append(row)

        # Create Table
        t = Table(table_data, colWidths=[1.2*inch, 0.8*inch]*3)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ACCENT_COLOR),
            ('BACKGROUND', (0,1), (-1,-1), NEUTRAL_LIGHT),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.white),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEUTRAL_LIGHT, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

    # --- Prediction Result ---
    if meta:
        story.append(Paragraph("Résultat de l'Analyse", styles['SectionHeader']))
        
        pred_val = meta.get('Prediction', 'N/A')
        prob_val = meta.get('Probability', 'N/A')
        model_name = meta.get('Model', 'N/A')
        
        is_risk = pred_val == '1' or pred_val == 'Yes' or pred_val == 'Risque'
        
        res_color = DANGER_COLOR if is_risk else SUCCESS_COLOR
        res_text = "⚠ RISQUE DÉTECTÉ" if is_risk else "✓ AUCUN RISQUE DÉTECTÉ"
        
        # Big Badge with colored background
        res_style = ParagraphStyle(
            name='ResultBadge',
            parent=styles['Normal'],
            fontSize=18,
            leading=22,
            textColor=colors.white,
            backColor=res_color,
            alignment=TA_CENTER,
            borderPadding=(10, 10, 10, 10),
            borderRadius=8,
            spaceAfter=10
        )
        story.append(Paragraph(f"<b>{res_text}</b>", res_style))
        story.append(Paragraph(f"Probabilité estimée : {float(prob_val)*100:.1f}%", styles['BodyText']))
        story.append(Paragraph(f"Modèle utilisé : {model_name}", styles['NormalSmall']))
        story.append(Spacer(1, 20))

    # --- Page Break before Analysis ---
    story.append(PageBreak())

    # --- SHAP Section ---
    story.append(Paragraph("1. Analyse Globale (SHAP)", styles['SectionHeader']))
    story.append(Paragraph("L'analyse SHAP montre comment chaque facteur contribue à pousser la prédiction vers le risque (rouge) ou vers la sécurité (vert), basé sur une compréhension globale du modèle.", styles['Normal']))
    story.append(Spacer(1, 10))
    
    if shap_fig:
        try:
            img_bytes = _fig_to_png_bytes(shap_fig)
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=3*inch)
            story.append(img)
        except Exception as e:
            import traceback
            print(f"[ERROR] SHAP chart rendering failed: {e}")
            traceback.print_exc()
            story.append(Paragraph(f"[Erreur rendu graphique SHAP: {str(e)}]", styles['Normal']))

    # Top Features Text SHAP
    if shap_explanation and 'top_features' in shap_explanation:
        story.append(Spacer(1, 5))
        story.append(Paragraph("Facteurs principaux (SHAP):", styles['Heading4']))
        for item in shap_explanation['top_features'][:5]:
            val = item.get('shap_value', 0)
            feat = item.get('feature', 'N/A')
            direction = "Risque" if val > 0 else "Sûr"
            txt = f"• {feat}: {abs(val):.3f} ({direction})"
            story.append(Paragraph(txt, styles['NormalSmall']))
            
    story.append(PageBreak())

    # --- LIME Section ---
    if lime_explanation or lime_fig:
        story.append(Paragraph("2. Analyse Locale (LIME)", styles['SectionHeader']))
        story.append(Paragraph("L'analyse LIME observe l'impact spécifique des valeurs de ce patient en perturbant localement les données pour isoler les facteurs décisifs.", styles['Normal']))
        story.append(Spacer(1, 10))

        if lime_fig:
            try:
                img_bytes = _fig_to_png_bytes(lime_fig)
                img = Image(io.BytesIO(img_bytes), width=6*inch, height=3*inch)
                story.append(img)
            except Exception as e:
                import traceback
                print(f"[ERROR] LIME chart rendering failed: {e}")
                traceback.print_exc()
                story.append(Paragraph(f"[Erreur rendu graphique LIME: {str(e)}]", styles['Normal']))
        
        # Top Features Text LIME
        if lime_explanation and 'explanation' in lime_explanation:
            story.append(Spacer(1, 5))
            story.append(Paragraph("Facteurs décisifs (LIME):", styles['Heading4']))
            # Assuming lime_explanation['explanation'] is sorted
            top_lime = lime_explanation['explanation'][:5]
            for item in top_lime:
                val = item.get('value', 0)
                feat = item.get('feature', 'N/A')
                direction = "Risque" if val > 0 else "Sûr"
                txt = f"• {feat}: {abs(val):.3f} ({direction})"
                story.append(Paragraph(txt, styles['NormalSmall']))

    # --- Page Break before Medical Info ---
    story.append(PageBreak())

    # --- Medical Information Section ---
    story.append(Paragraph("Informations Médicales de Référence", styles['SectionHeader']))
    story.append(Spacer(1, 10))
    
    # Causes
    story.append(Paragraph("Causes reconnues officiellement", styles['Heading3']))
    story.append(Paragraph("Les docteurs et chercheurs s'accordent sur les causes suivantes :", styles['Normal']))
    story.append(Spacer(1, 5))
    
    causes = [
        "Rayons UV (UVA et UVB) - cause principale",
        "Bronzage artificiel (cabines UV)",
        "Prédisposition génétique",
        "Peau claire, nombreux grains de beauté",
        "Système immunitaire affaibli",
        "Coups de soleil répétés (surtout dans l'enfance)"
    ]
    for cause in causes:
        story.append(Paragraph(f"• {cause}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # ABCDE Signs
    story.append(Paragraph("Signes d'alerte reconnus par les dermatologues", styles['Heading3']))
    story.append(Paragraph("Les médecins utilisent la règle ABCDE pour le mélanome :", styles['Normal']))
    story.append(Spacer(1, 5))
    
    abcde = [
        "<b>A</b> : Asymétrie",
        "<b>B</b> : Bords irréguliers",
        "<b>C</b> : Couleur non homogène",
        "<b>D</b> : Diamètre > 6 mm",
        "<b>E</b> : Évolution (taille, couleur, forme)"
    ]
    for sign in abcde:
        story.append(Paragraph(f"• {sign}", styles['Normal']))
    
    story.append(Spacer(1, 5))
    story.append(Paragraph("Toute lésion qui change doit être examinée.", styles['Normal']))
    story.append(Spacer(1, 15))
    
    # Diagnosis
    story.append(Paragraph("Diagnostic officiel", styles['Heading3']))
    diagnostics = [
        "Examen clinique dermatologique",
        "Dermoscopie",
        "Biopsie (seul diagnostic de certitude)",
        "Imagerie si suspicion de métastases"
    ]
    for diag in diagnostics:
        story.append(Paragraph(f"• {diag}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # Treatments
    story.append(Paragraph("Traitements reconnus", styles['Heading3']))
    story.append(Paragraph("Selon le stade :", styles['Normal']))
    story.append(Spacer(1, 5))
    
    treatments = [
        "Chirurgie (traitement principal)",
        "Radiothérapie",
        "Immunothérapie (mélanome avancé)",
        "Thérapies ciblées",
        "Chimiothérapie (cas spécifiques)"
    ]
    for treat in treatments:
        story.append(Paragraph(f"• {treat}", styles['Normal']))
    
    story.append(Spacer(1, 15))
    
    # Prevention
    story.append(Paragraph("Prévention (recommandations officielles)", styles['Heading3']))
    story.append(Paragraph("Les médecins recommandent :", styles['Normal']))
    story.append(Spacer(1, 5))
    
    prevention = [
        "Éviter le soleil entre 11h et 16h",
        "Utiliser un écran solaire SPF 30–50",
        "Porter chapeau, lunettes, vêtements couvrants",
        "Ne jamais utiliser de cabines UV",
        "Surveillance régulière de la peau",
        "Consultation dermatologique annuelle si à risque"
    ]
    for prev in prevention:
        story.append(Paragraph(f"• {prev}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Page Break before Sources
    story.append(PageBreak())
    
    # Sources
    story.append(Paragraph("Sources officielles", styles['Heading4']))
    story.append(Paragraph(
        "• <b>Cancer.fr</b> (site officiel sur le cancer) : explication des types de cancers de la peau, "
        "rôle des rayons UV et importance du dépistage.",
        styles['NormalSmall']
    ))
    story.append(Paragraph(
        "📌 <link href='https://www.cancer.fr/toute-l-information-sur-les-cancers/se-faire-depister/les-depistages/depistage-des-cancers-de-la-peau/les-cancers-de-la-peau'>https://www.cancer.fr/toute-l-information-sur-les-cancers/se-faire-depister/les-depistages/depistage-des-cancers-de-la-peau/les-cancers-de-la-peau</link>",
        styles['NormalSmall']
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "• <b>CDC</b> (Centers for Disease Control and Prevention, USA) : types de cancer de la peau, "
        "causes (UV), prévention et diagnostic.",
        styles['NormalSmall']
    ))
    story.append(Paragraph(
        "<link href='https://www.cdc.gov/skin-cancer/about/index.html'>https://www.cdc.gov/skin-cancer/about/index.html</link>",
        styles['NormalSmall']
    ))

    # --- Footer / Disclaimer ---
    story.append(Spacer(1, 30))
    story.append(Paragraph("Avertissement", styles['Heading4']))
    disclaimer = ("Ce document est généré automatiquement par un système d'intelligence artificielle. "
                  "Il ne remplace en aucun cas un diagnostic médical professionnel. "
                  "Veuillez consulter un dermatologue pour une interprétation clinique.")
    story.append(Paragraph(disclaimer, styles['NormalSmall']))

    # Build PDF
    doc.build(story)
    
    return buffer.getvalue()
