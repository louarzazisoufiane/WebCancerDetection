
"""
Route for Image Classification (Skin Cancer)
"""
from flask import Blueprint, render_template, request, jsonify
import tensorflow as tf
import joblib
import numpy as np
from PIL import Image
import io
import os
from app_module.config.settings import Config

image_bp = Blueprint('image_bp', __name__)

# Global model variable
params = {
    "model": None,
    "img_size": 236
}

def load_model():
    """Lazy load the Keras model from the pickle file."""
    if params["model"] is None:
        try:
            model_path = os.path.join(Config.BASE_DIR, 'mymodel.pkl')
            # Load the pickled model (which is a tf.keras model structure)
            # joblib loading of keras models depends on environment
            # If it fails, we might need to rely on the fact it was saved on a similar env or use custom loading
            
            # Since the user provided mymodel.pkl using joblib.dump(cnn, ...), we assume consistent tf version
            params["model"] = joblib.load(model_path)
            print("Image Classification Model loaded successfully.")
        except Exception as e:
            print(f"Error loading image model: {e}")

@image_bp.route('/image-analysis/')
def index():
    """Render the image analysis page."""
    return render_template('image_predict.html')

@image_bp.route('/api/predict-image', methods=['POST'])
def predict_image():
    """API Endpoint for image prediction."""
    # Ensure model is loaded
    if params["model"] is None:
        load_model()
    
    if params["model"] is None:
        return jsonify({'error': 'Model could not be loaded'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # 1. Read Image
        image_bytes = file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # 2. Preprocess (Resize 236x236, Normalize)
        img = img.resize((params["img_size"], params["img_size"]))
        img_array = np.array(img) / 255.0
        
        # Add batch dimension (1, 236, 236, 3)
        img_batch = np.expand_dims(img_array, axis=0)
        
        # 3. Predict
        prediction_prob = params["model"].predict(img_batch)[0][0]
        
        # 4. Interpret Result (0=Benign, 1=Malignant)
        # We can define a threshold, e.g., 0.5
        is_malignant = prediction_prob > 0.5
        
        # Calculate percentages
        malignancy_prob_percent = float(prediction_prob) * 100
        benign_prob_percent = (1 - float(prediction_prob)) * 100
        
        result = {
            'probability': float(prediction_prob),
            'malignancy_probability_percent': malignancy_prob_percent,
            'benign_probability_percent': benign_prob_percent,
            'prediction': 'Malignant' if is_malignant else 'Benign',
            'label': 'Maligne' if is_malignant else 'Bénigne', # French label
            'confidence': float(prediction_prob if is_malignant else 1 - prediction_prob) * 100
        }
        
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': str(e)}), 500
