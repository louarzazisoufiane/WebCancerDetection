import streamlit as st
import pandas as pd
import joblib
import sys
import types

# Page configuration
st.set_page_config(
    page_title="SmartCheck Health Prediction",
    page_icon="🏥",
    layout="wide"
)

# Binary transform function
def binary_transform(df):
    return df.applymap(lambda x: 1 if x == "Yes" else 0)

# Make binary_transform available for unpickling
try:
    main_mod = sys.modules.get('__main__')
    if main_mod is None:
        main_mod = types.ModuleType('__main__')
        sys.modules['__main__'] = main_mod
    setattr(main_mod, 'binary_transform', binary_transform)
except Exception:
    pass

# Load models (with caching for performance)
@st.cache_resource
def load_models():
    return {
        "Logistic Regression": joblib.load("models/pipeline_logistic_regression.pkl"),
        "Random Forest": joblib.load("models/pipeline_random_forest.pkl"),
        "Gradient Boosting": joblib.load("models/pipeline_gradient_boosting.pkl"),
        "KNN": joblib.load("models/pipeline_knn.pkl")
    }

try:
    MODELS = load_models()
except Exception as e:
    st.error(f"Error loading models: {e}")
    st.stop()

def prepare_input(data):
    """Prepare input DataFrame from form data"""
    df_data = {
        'HeartDisease': [data['HeartDisease']],
        'BMI': [float(data['BMI'])],
        'Smoking': [data['Smoking']],
        'AlcoholDrinking': ['No'],
        'Stroke': ['No'],
        'PhysicalHealth': [0.0],
        'MentalHealth': [0.0],
        'DiffWalking': ['No'],
        'Sex': [data['Sex']],
        'AgeCategory': [data['AgeCategory']],
        'Race': ['White'],
        'Diabetic': ['No'],
        'PhysicalActivity': [data['PhysicalActivity']],
        'GenHealth': [data['GenHealth']],
        'SleepTime': [7.0],
        'Asthma': ['No'],
        'KidneyDisease': ['No']
    }
    return pd.DataFrame(df_data)

# Main app
st.title("🏥 SmartCheck Health Prediction")
st.markdown("### Predict health risk based on your personal information")

# Sidebar for model selection
st.sidebar.header("Model Configuration")
model_choice = st.sidebar.selectbox(
    "Choose prediction model:",
    list(MODELS.keys())
)

# Main form
st.header("Patient Information")

col1, col2 = st.columns(2)

with col1:
    sex = st.selectbox("Sex", ["Male", "Female"])
    age_category = st.selectbox(
        "Age Category",
        ["18-24", "25-29", "30-34", "35-39", "40-44", 
         "45-49", "50-54", "55-59", "60-64", "65-69", 
         "70-74", "75-79", "80 or older"]
    )
    bmi = st.number_input("BMI (Body Mass Index)", min_value=10.0, max_value=60.0, value=25.0, step=0.1)
    heart_disease = st.selectbox("Heart Disease", ["No", "Yes"])

with col2:
    smoking = st.selectbox("Smoking", ["No", "Yes"])
    physical_activity = st.selectbox("Physical Activity", ["No", "Yes"])
    gen_health = st.selectbox(
        "General Health",
        ["Excellent", "Very good", "Good", "Fair", "Poor"]
    )

# Prediction button
if st.button("🔍 Predict Health Risk", type="primary", use_container_width=True):
    # Prepare input data
    input_data = {
        'Sex': sex,
        'AgeCategory': age_category,
        'BMI': bmi,
        'HeartDisease': heart_disease,
        'Smoking': smoking,
        'PhysicalActivity': physical_activity,
        'GenHealth': gen_health
    }
    
    df_input = prepare_input(input_data)
    
    # Make prediction
    try:
        pipeline = MODELS[model_choice]
        prediction = pipeline.predict(df_input)[0]
        
        if hasattr(pipeline, "predict_proba"):
            probability = pipeline.predict_proba(df_input)[0][1]
        else:
            probability = None
        
        # Display results
        st.markdown("---")
        st.header("📊 Prediction Results")
        
        # Result cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Model Used", model_choice)
        
        with col2:
            result_label = "⚠️ At Risk" if prediction == 1 else "✅ Healthy"
            st.metric("Prediction", result_label)
        
        with col3:
            if probability is not None:
                prob_percent = f"{probability * 100:.1f}%"
                st.metric("Risk Probability", prob_percent)
        
        # Detailed explanation
        if prediction == 1:
            st.error("⚠️ **Warning**: The model predicts an elevated health risk. Please consult with a healthcare professional.")
        else:
            st.success("✅ **Good News**: The model predicts a low health risk. Continue maintaining healthy habits!")
        
        # Display input summary
        with st.expander("📋 Input Summary"):
            st.json(input_data)
        
        # Optional: Add explanations if available
        try:
            from app_module.utils.xai import explain_model_prediction
            explanation = explain_model_prediction(pipeline, df_input)
            
            if explanation and 'all_features' in explanation:
                st.subheader("🔍 Feature Importance (SHAP)")
                
                # Show top features
                top_features = explanation['all_features'][:5]
                for feat in top_features:
                    st.write(f"**{feat['feature']}**: {feat['shap_value']:.4f}")
        except ImportError:
            st.info("Install SHAP for detailed explanations: `pip install shap`")
        except Exception as e:
            st.warning(f"Could not generate explanation: {e}")
            
    except Exception as e:
        st.error(f"Error making prediction: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>⚕️ This is a prediction tool and should not replace professional medical advice.</p>
    </div>
    """,
    unsafe_allow_html=True
)
