import joblib
import numpy as np
from PIL import Image
import os
import sys

# Define parameters matching the app
IMG_SIZE = 236
MODEL_PATH = '/home/sebabte/canc/mymodel.pkl'
IMAGE_PATH = '/home/sebabte/.gemini/antigravity/brain/4d0b4cc2-632b-40f1-9592-1e6726ef3238/uploaded_image_1765679977202.png'

def predict():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}")
        return
    if not os.path.exists(IMAGE_PATH):
        print(f"Image not found at {IMAGE_PATH}")
        return

    print("Loading model...")
    try:
        model = joblib.load(MODEL_PATH)
        print("Model loaded.")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print("Processing image...")
    try:
        img = Image.open(IMAGE_PATH).convert('RGB')
        img = img.resize((IMG_SIZE, IMG_SIZE))
        img_array = np.array(img) / 255.0
        img_batch = np.expand_dims(img_array, axis=0)
        
        print(f"Input shape: {img_batch.shape}")
        print(f"Input min/max: {img_batch.min()}, {img_batch.max()}")

        print("Predicting...")
        prediction_prob = model.predict(img_batch)[0][0]
        
        print(f"Raw Prediction Probability: {prediction_prob}")
        print(f"Formatted Probability: {prediction_prob:.10f}")
        print(f"Result: {'Malignant' if prediction_prob > 0.5 else 'Benign'}")
        
    except Exception as e:
        print(f"Prediction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    predict()
