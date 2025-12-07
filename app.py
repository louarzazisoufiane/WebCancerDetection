from flask import Flask, render_template, request, jsonify, redirect
import pandas as pd
import joblib
from app_module.utils.xai import explain_model_prediction
from app_module.utils.report import generate_professional_pdf
import plotly.graph_objects as go

app = Flask(__name__)

def binary_transform(df):
    return df.applymap(lambda x: 1 if x == "Yes" else 0)

MODELS = {
    "log_reg": joblib.load("models/pipeline_logistic_regression.pkl"),
    "random_forest": joblib.load("models/pipeline_random_forest.pkl"),
    "gradient_boosting": joblib.load("models/pipeline_gradient_boosting.pkl"),
    "knn": joblib.load("models/pipeline_knn.pkl")
}

def prepare_input(form):
    data = {
        'HeartDisease': [form['HeartDisease']],
        'BMI': [float(form['BMI'])],
        'Smoking': [form['Smoking']],
        'AlcoholDrinking': ['No'],
        'Stroke': ['No'],
        'PhysicalHealth': [0.0],
        'MentalHealth': [0.0],
        'DiffWalking': ['No'],
        'Sex': [form['Sex']],
        'AgeCategory': [form['AgeCategory']],
        'Race': ['White'],
        'Diabetic': ['No'],
        'PhysicalActivity': [form['PhysicalActivity']],
        'GenHealth': [form['GenHealth']],
        'SleepTime': [7.0],
        'Asthma': ['No'],
        'KidneyDisease': ['No']
    }
    return pd.DataFrame(data)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        form = request.form
        df_input = prepare_input(form)
        
        pipeline = MODELS[form['model_choice']]
        
        pred = pipeline.predict(df_input)[0]
        prob = pipeline.predict_proba(df_input)[0][1] if hasattr(pipeline, "predict_proba") else "N/A"
        
        result = {'prediction': int(pred), 'probability': round(prob, 3) if prob != "N/A" else "N/A"}
    
    return render_template('index.html', result=result)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint pour les prédictions en JSON"""
    try:
        # Accept either form-encoded or JSON payloads
        data = request.get_json(silent=True)
        if data:
            # If JSON, use keys directly
            model_choice = data.get('model_choice', 'log_reg')
            df_input = prepare_input(data)
        else:
            form = request.form
            model_choice = form.get('model_choice', 'log_reg')
            df_input = prepare_input(form)

        pipeline = MODELS.get(model_choice, MODELS['log_reg'])

        pred = pipeline.predict(df_input)[0]
        prob = pipeline.predict_proba(df_input)[0][1] if hasattr(pipeline, "predict_proba") else 0

        # Compute SHAP explanation (lightweight) and include values
        try:
            explanation = explain_model_prediction(pipeline, df_input)
        except Exception as e:
            explanation = {'error': f'Failed to compute explanation: {str(e)}'}

        return jsonify({
            'success': True,
            'prediction': int(pred),
            'probability': float(prob),
            'model': model_choice,
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/report', methods=['POST'])
def report():
    """Generate a professional PDF report for the given input (form or JSON)."""
    try:
        data = request.get_json(silent=True)
        if data:
            model_choice = data.get('model_choice', 'log_reg')
            df_input = prepare_input(data)
        else:
            form = request.form
            model_choice = form.get('model_choice', 'log_reg')
            df_input = prepare_input(form)

        pipeline = MODELS.get(model_choice, MODELS['log_reg'])

        # predict
        pred = pipeline.predict(df_input)[0]
        prob = pipeline.predict_proba(df_input)[0][1] if hasattr(pipeline, 'predict_proba') else None

        # explanation
        explanation = explain_model_prediction(pipeline, df_input)

        # build bar chart if possible
        fig = None
        if explanation and 'all_features' in explanation:
            feats = [it['feature'] for it in explanation['all_features']]
            vals = [it['shap_value'] for it in explanation['all_features']]
            fig = go.Figure(go.Bar(x=vals, y=feats, orientation='h', marker_color=['#f56565' if v>=0 else '#38a169' for v in vals]))
            fig.update_layout(margin=dict(l=200, r=20, t=20, b=20), height=800)

        meta = {
            'Model': model_choice,
            'Prediction': str(int(pred)),
            'Probability': f"{prob:.3f}" if prob is not None else 'N/A'
        }

        pdf = generate_professional_pdf('Rapport XAI - Prédiction', explanation, fig, meta)

        return (pdf, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="xai_report.pdf"'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Enregistrer le dashboard modular
from app_module.routes.dashboard import dashboard_bp
dashboard_bp(app)

# Redirection pour /dashboard sans slash final
@app.route('/dashboard')
def redirect_dashboard():
    return redirect('/dashboard/')

# Page d'accueil Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
