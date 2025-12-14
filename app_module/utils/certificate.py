"""
Génération de certificat/image pour les tests médicaux
"""
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from typing import Dict, Any, Optional
from app_module.config.settings import Config


def generate_certificate_image(
    test_id: int,
    prediction: int,
    probability: float,
    model_used: str,
    timestamp: str,
    input_features: Dict[str, Any]
) -> str:
    """
    Génère une image de certificat pour le test médical
    
    Returns:
        str: Chemin relatif vers l'image générée
    """
    # Créer le répertoire pour les certificats
    cert_dir = os.path.join(Config.BASE_DIR, 'data', 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    
    # Dimensions de l'image
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Couleurs orange professionnelles
    primary_color = (255, 107, 53)  # #FF6B35
    secondary_color = (255, 140, 66)  # #FF8C42
    dark_text = (31, 41, 55)  # #1F2937
    light_text = (113, 128, 150)  # #718096
    
    # En-tête avec dégradé orange
    header_height = 150
    for y in range(header_height):
        ratio = y / header_height
        r = int(255 - (255 - 255) * ratio)
        g = int(107 - (107 - 140) * ratio)
        b = int(53 - (53 - 66) * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Titre principal - Essayer différentes polices
    title_font = None
    subtitle_font = None
    text_font = None
    small_font = None
    
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "arial.ttf"
    ]
    
    try:
        for path in font_paths:
            try:
                title_font = ImageFont.truetype(path, 36)
                subtitle_font = ImageFont.truetype(path.replace('Bold', '').replace('-Bold', ''), 20)
                text_font = ImageFont.truetype(path.replace('Bold', '').replace('-Bold', ''), 16)
                small_font = ImageFont.truetype(path.replace('Bold', '').replace('-Bold', ''), 14)
                break
            except:
                continue
    except:
        pass
    
    # Fallback si aucune police n'est trouvée
    if not title_font:
        try:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        except:
            # Dernier recours
            title_font = None
            subtitle_font = None
            text_font = None
            small_font = None
    
    # Titre
    title = "CERTIFICAT DE TEST MEDICAL"
    if title_font:
        try:
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
        except:
            title_width = len(title) * 20  # Estimation
        draw.text(((width - title_width) // 2, 30), title, fill='white', font=title_font)
    else:
        draw.text((width // 2 - 150, 30), title, fill='white')
    
    subtitle = "Prediction du Cancer de la Peau"
    if subtitle_font:
        try:
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        except:
            subtitle_width = len(subtitle) * 12
        draw.text(((width - subtitle_width) // 2, 80), subtitle, fill='white', font=subtitle_font)
    else:
        draw.text((width // 2 - 120, 80), subtitle, fill='white')
    
    # Contenu principal
    y_position = 200
    
    # Numéro de test
    draw.text((50, y_position), f"Numero de Test: #{test_id}", fill=dark_text, font=text_font)
    y_position += 40
    
    # Date
    draw.text((50, y_position), f"Date: {timestamp}", fill=dark_text, font=text_font)
    y_position += 40
    
    # Résultat
    result_text = "RISQUE DETECTE" if prediction == 1 else "AUCUN RISQUE IDENTIFIE"
    result_color = (239, 68, 68) if prediction == 1 else (16, 185, 129)  # Rouge ou Vert
    draw.text((50, y_position), "Resultat:", fill=dark_text, font=text_font)
    draw.text((200, y_position), result_text, fill=result_color, font=text_font)
    y_position += 50
    
    # Probabilité
    prob_text = f"Probabilite: {probability * 100:.1f}%"
    draw.text((50, y_position), prob_text, fill=dark_text, font=text_font)
    y_position += 40
    
    # Modèle utilisé
    draw.text((50, y_position), f"Modele utilise: {model_used}", fill=light_text, font=small_font)
    y_position += 60
    
    # Ligne de séparation
    draw.line([(50, y_position), (width - 50, y_position)], fill=(254, 215, 170), width=2)
    y_position += 30
    
    # Informations du patient (features principales)
    draw.text((50, y_position), "Informations du Test:", fill=dark_text, font=text_font)
    y_position += 35
    
    # Afficher les features principales
    key_features = ['BMI', 'AgeCategory', 'Sex', 'GenHealth', 'Smoking', 'PhysicalActivity']
    for feature in key_features:
        if feature in input_features:
            value = str(input_features[feature])
            # Limiter la longueur pour éviter les débordements
            if len(value) > 30:
                value = value[:27] + "..."
            if small_font:
                draw.text((70, y_position), f"- {feature}: {value}", fill=light_text, font=small_font)
            else:
                draw.text((70, y_position), f"- {feature}: {value}", fill=light_text)
            y_position += 25
    
    y_position += 30
    
    # Ligne de séparation
    draw.line([(50, y_position), (width - 50, y_position)], fill=(254, 215, 170), width=2)
    y_position += 40
    
    # Avertissement
    warning_text = "Ce document est une preuve de test medical effectue."
    if small_font:
        try:
            warning_bbox = draw.textbbox((0, 0), warning_text, font=small_font)
            warning_width = warning_bbox[2] - warning_bbox[0]
        except:
            warning_width = len(warning_text) * 8
        draw.text(((width - warning_width) // 2, y_position), warning_text, fill=light_text, font=small_font)
    else:
        draw.text((width // 2 - 150, y_position), warning_text, fill=light_text)
    
    y_position += 30
    
    # Note importante
    note_text = "Consultez un professionnel de sante pour un diagnostic medical complet."
    if small_font:
        try:
            note_bbox = draw.textbbox((0, 0), note_text, font=small_font)
            note_width = note_bbox[2] - note_bbox[0]
        except:
            note_width = len(note_text) * 8
        draw.text(((width - note_width) // 2, y_position), note_text, fill=light_text, font=small_font)
    else:
        draw.text((width // 2 - 200, y_position), note_text, fill=light_text)
    
    # Pied de page
    footer_y = height - 80
    footer_text = "Document genere automatiquement"
    if small_font:
        draw.text((width // 2 - 100, footer_y), footer_text, fill=light_text, font=small_font)
    else:
        draw.text((width // 2 - 100, footer_y), footer_text, fill=light_text)
    
    # Sauvegarder l'image
    filename = f"certificate_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(cert_dir, filename)
    img.save(filepath, 'PNG', quality=95)
    
    # Retourner le chemin relatif
    return f"certificates/{filename}"


def generate_certificate_from_result(test_data: Dict[str, Any]) -> str:
    """Génère un certificat à partir des données d'un test"""
    return generate_certificate_image(
        test_id=test_data.get('test_id', 0),
        prediction=test_data.get('prediction', 0),
        probability=test_data.get('probability', 0.0),
        model_used=test_data.get('model', 'unknown'),
        timestamp=test_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        input_features=test_data.get('input_features', {})
    )

