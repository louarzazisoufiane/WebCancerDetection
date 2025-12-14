from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
import pandas as pd
import joblib
from app_module.utils.xai import explain_model_prediction, explain_model_prediction_lime
from app_module.utils.report import generate_professional_pdf
from app_module.utils.database import db
from app_module.utils.certificate import generate_certificate_from_result
import plotly.graph_objects as go
import os
from datetime import datetime
from app_module.config.settings import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

def binary_transform(df):
    return df.applymap(lambda x: 1 if x == "Yes" else 0)

# Ensure `binary_transform` is available under the `__main__` module name so
# joblib/pickle can resolve references to `__main__.binary_transform` when
# unpickling models that were saved from a script run as __main__.
import sys, types
try:
    # Prefer attaching to existing __main__ module if present
    main_mod = sys.modules.get('__main__')
    if main_mod is None:
        main_mod = types.ModuleType('__main__')
        sys.modules['__main__'] = main_mod
    setattr(main_mod, 'binary_transform', binary_transform)
except Exception:
    # Best-effort: if attaching fails, continue and let unpickle throw a clear error
    pass

# Load models after ensuring pickled dependencies are resolvable
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

        # Compute LIME explanation
        try:
            lime_explanation = explain_model_prediction_lime(pipeline, df_input)
        except Exception as e:
            lime_explanation = {'error': f'Failed to compute LIME: {str(e)}'}

        # Sauvegarder le test dans la base de données
        test_id = None
        certificate_path = None
        try:
            # Préparer les features pour la sauvegarde
            input_features = df_input.to_dict('records')[0] if not df_input.empty else {}
            user_ip = request.remote_addr
            
            # Sauvegarder le test
            test_id = db.save_test(
                model_used=model_choice,
                prediction=int(pred),
                probability=float(prob),
                input_features=input_features,
                explanation=explanation if 'error' not in explanation else None,
                certificate_path=None,  # Sera mis à jour après génération
                user_ip=user_ip
            )
            
            # Générer le certificat
            test_data = {
                'test_id': test_id,
                'prediction': int(pred),
                'probability': float(prob),
                'model': model_choice,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'input_features': input_features
            }
            certificate_path = generate_certificate_from_result(test_data)
            
            # Mettre à jour le test avec le chemin du certificat
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE tests SET certificate_path = ? WHERE id = ?', (certificate_path, test_id))
            conn.commit()
            conn.close()
            
        except Exception as e:
            # Ne pas faire échouer la requête si la sauvegarde échoue
            import traceback
            print(f"[ERROR] Erreur lors de la sauvegarde du test: {e}")
            traceback.print_exc()
            # Logger l'erreur mais continuer

        return jsonify({
            'success': True,
            'prediction': int(pred),
            'probability': float(prob),
            'model': model_choice,
            'explanation': explanation,
            'lime_explanation': lime_explanation,
            'test_id': test_id,
            'certificate_path': certificate_path
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

        # Explanation SHAP
        explanation = explain_model_prediction(pipeline, df_input)

        # SHAP Chart
        shap_fig = None
        if explanation and 'all_features' in explanation:
            feats = [it['feature'] for it in explanation['all_features'][:10]] # Top 10
            vals = [it['shap_value'] for it in explanation['all_features'][:10]]
            # Reverse for horizontal bar chart
            feats.reverse()
            vals.reverse()
            colors = ['#ef4444' if v>=0 else '#10b981' for v in vals]
            
            shap_fig = go.Figure(go.Bar(x=vals, y=feats, orientation='h', marker_color=colors))
            shap_fig.update_layout(
                title="SHAP - Importance Globale",
                margin=dict(l=150, r=20, t=40, b=20), 
                height=400,
                xaxis_title="Impact sur la prédiction"
            )

        # Explanation LIME
        lime_explanation = {}
        lime_fig = None
        try:
            lime_explanation = explain_model_prediction_lime(pipeline, df_input)
            if 'explanation' in lime_explanation:
                l_data = lime_explanation['explanation'][:10] # Top 10
                l_feats = [it['feature'] for it in l_data]
                l_vals = [it['value'] for it in l_data]
                # Reverse
                l_feats.reverse()
                l_vals.reverse()
                l_colors = ['#ef4444' if v>=0 else '#3b82f6' for v in l_vals] # Blue/Red for LIME
                
                lime_fig = go.Figure(go.Bar(x=l_vals, y=l_feats, orientation='h', marker_color=l_colors))
                lime_fig.update_layout(
                    title="LIME - Impact Local",
                    margin=dict(l=150, r=20, t=40, b=20), 
                    height=400,
                    xaxis_title="Poids local"
                )
        except Exception as e:
            print(f"Error producing LIME for report: {e}")

        meta = {
            'Model': model_choice,
            'Prediction': "Risque" if int(pred) == 1 else "Sain",
            'Probability': f"{prob:.3f}" if prob is not None else 'N/A'
        }
        
        # Prepare input data summary (convert df to dict)
        input_summary = df_input.to_dict(orient='records')[0]

        pdf = generate_professional_pdf(
            title='Rapport d\'Analyse SmartCheck', 
            shap_explanation=explanation, 
            lime_explanation=lime_explanation,
            shap_fig=shap_fig, 
            lime_fig=lime_fig,
            meta=meta,
            input_data=input_summary
        )

        return (pdf, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="SkinCheck_Vision_Report.pdf"'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Enregistrer le dashboard modular
from app_module.routes.dashboard import dashboard_bp
dashboard_bp(app)

# Enregistrer les routes admin
from app_module.routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Enregistrer les routes image classification
from app_module.routes.image_prediction import image_bp
app.register_blueprint(image_bp)

# Route pour servir les certificats (public, pour téléchargement)
@app.route('/certificates/<path:filename>')
def serve_certificate(filename):
    """Servir les certificats (accessible publiquement pour téléchargement)"""
    cert_dir = os.path.join(Config.BASE_DIR, 'data', 'certificates')
    return send_from_directory(cert_dir, filename)

# Redirection pour /dashboard sans slash final
@app.route('/dashboard')
def redirect_dashboard():
    return redirect('/dashboard/')

# Page d'accueil Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
