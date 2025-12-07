"""
XAI helpers using SHAP to compute per-feature contributions for a prediction.
"""
import pandas as pd
from typing import Any, Dict
import shap
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from app_module.config.settings import Config


def explain_model_prediction(model: Any, df_input: pd.DataFrame, n_background: int = 100) -> Dict[str, Any]:
    """Return SHAP contributions for a single-row input DataFrame.

    Returns a dict with keys:
      - base_value: model base value (if available)
      - all_features: list of {feature, shap_value} for every feature (sorted by abs desc)
      - top_features: top 5 features (subset of all_features)

    This function uses shap.Explainer which will pick an appropriate explainer
    (TreeExplainer for tree models, Kernel or Linear otherwise).
    """
    try:
        # Try to read a background dataset to improve explainer quality
        try:
            df_full = pd.read_csv(Config.DATASET_PATH)
            # Keep columns common with input
            common_cols = [c for c in df_input.columns if c in df_full.columns]
            if common_cols:
                bg = df_full[common_cols]
            else:
                bg = df_input
            if bg.shape[0] > n_background:
                bg = bg.sample(n=n_background, random_state=42)
        except Exception:
            bg = df_input

        # Ensure same column order
        try:
            bg = bg[df_input.columns]
        except Exception:
            pass

        # If the model is a scikit-learn Pipeline with a preprocessing step,
        # transform inputs first so SHAP receives numeric arrays instead of strings.
        explainer = None
        feature_names = list(df_input.columns)

        preprocess = None
        clf = None
        explainer_type = None
        if hasattr(model, 'named_steps'):
            preprocess = model.named_steps.get('preprocess')
            clf = model.named_steps.get('clf')

        def _get_transformed_feature_names(preprocess, input_columns):
            """Attempt to recover human-friendly feature names after transformation.

            Returns a list of names. Falls back to generic names if unavailable.
            """
            try:
                # Preferred: the preprocess exposes get_feature_names_out
                if hasattr(preprocess, 'get_feature_names_out'):
                    return list(preprocess.get_feature_names_out(input_columns))
            except Exception:
                pass

            names = []
            try:
                # ColumnTransformer: iterate transformers_
                for name, trans, cols in preprocess.transformers_:
                    if name == 'remainder' or trans == 'drop':
                        continue
                    # Try to get a list of column names
                    try:
                        cols_list = list(cols)
                    except Exception:
                        # fallback to input columns
                        cols_list = list(input_columns)

                    if hasattr(trans, 'get_feature_names_out'):
                        try:
                            out = trans.get_feature_names_out(cols_list)
                        except Exception:
                            try:
                                out = trans.get_feature_names_out()
                            except Exception:
                                out = [f"{name}__{c}" for c in cols_list]
                        names.extend([str(x) for x in out])
                    else:
                        # transformer doesn't expand columns
                        names.extend([f"{name}__{c}" for c in cols_list])
                return names
            except Exception:
                # give up and return generic names
                return [f'f{i}' for i in range(len(input_columns))]

        if preprocess is not None and clf is not None:
            # transform background and input
            try:
                bg_trans = preprocess.transform(bg)
                input_trans = preprocess.transform(df_input)
            except Exception:
                # fallback to numeric values if transform fails
                try:
                    bg_trans = np.asarray(bg)
                    input_trans = np.asarray(df_input)
                except Exception:
                    bg_trans = bg.values
                    input_trans = df_input.values

                # try to get feature names after transformation
                feature_names = _get_transformed_feature_names(preprocess, df_input.columns)

                # Format feature names to be human-readable (e.g., one-hot -> Feature=Value)
                def _pretty_name(n: str) -> str:
                    s = str(n)
                    # Remove common prefixes
                    for p in ('preprocess__', 'preprocess_', 'onehot__', 'onehot_', 'onehot-', 'remainder__'):
                        if s.startswith(p):
                            s = s[len(p):]
                            break

                    # patterns like transformer__col_val or col_val
                    if '__' in s:
                        # keep content after first __
                        s = s.split('__', 1)[1]

                    # If there's a single underscore separating column and value
                    if '_' in s:
                        parts = s.split('_', 1)
                        col = parts[0]
                        val = parts[1].replace('_', ' ')
                        return f"{col}={val}"

                    return s

                try:
                    feature_names = [_pretty_name(n) for n in feature_names]
                except Exception:
                    pass

            # Choose explainer: prefer TreeExplainer for tree-based classifiers
            tree_types = (RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier, DecisionTreeClassifier)
            clf_name = clf.__class__.__name__
            is_tree = isinstance(clf, tree_types) or any(k in clf_name for k in ('XGB', 'LGBM', 'CatBoost', 'Gradient'))

            if is_tree:
                try:
                    explainer = shap.TreeExplainer(clf, bg_trans)
                    explainer_type = 'TreeExplainer'
                    sv = explainer(input_trans)
                except Exception:
                    # fallback to functional wrapper
                    def _predict_proba_transformed(x):
                        arr = np.asarray(x)
                        probs = clf.predict_proba(arr)
                        try:
                            return probs[:, 1]
                        except Exception:
                            return probs

                    explainer = shap.Explainer(_predict_proba_transformed, bg_trans)
                    explainer_type = 'Auto(FunctionWrapper)'
                    sv = explainer(input_trans)
            else:
                # functional wrapper for non-tree classifiers
                def _predict_proba_transformed(x):
                    arr = np.asarray(x)
                    probs = clf.predict_proba(arr)
                    try:
                        return probs[:, 1]
                    except Exception:
                        return probs

                explainer = shap.Explainer(_predict_proba_transformed, bg_trans)
                explainer_type = 'Auto(FunctionWrapper)'
                sv = explainer(input_trans)
        else:
            # Non-pipeline or pipeline without named preprocess/clf: fall back
            if hasattr(model, 'predict_proba'):
                def _predict_proba_raw(x):
                    # shap may pass numpy arrays; convert to DataFrame with proper columns
                    try:
                        if isinstance(x, np.ndarray):
                            try:
                                x_df = pd.DataFrame(x, columns=df_input.columns)
                            except Exception:
                                x_df = pd.DataFrame(x)
                        else:
                            x_df = pd.DataFrame(x)
                    except Exception:
                        x_df = pd.DataFrame(x)

                    probs = model.predict_proba(x_df)
                    try:
                        return probs[:, 1]
                    except Exception:
                        return probs

                explainer = shap.Explainer(_predict_proba_raw, bg)
            else:
                explainer = shap.Explainer(model, bg)

            sv = explainer(df_input)

        # Extract values
        values = sv.values
        # Handle shape (n_outputs, n_features) or (n_samples, n_features)
        try:
            if hasattr(values, 'ndim') and values.ndim > 1:
                # If multiple dims, take first sample's first output when possible
                if values.shape[0] > 1 and values.shape[1] > 1:
                    vals = values[0]
                else:
                    vals = values
            else:
                vals = values
        except Exception:
            vals = values

        # Flatten to 1D list corresponding to features
        try:
            contribs = [float(v) for v in vals.flatten()]
        except Exception:
            contribs = [float(v) for v in vals]

        # feature_names should have been set earlier (either original columns
        # or transformed feature names). Ensure lengths match; otherwise
        # generate fallback generic names to avoid misalignment.
        if not feature_names or len(feature_names) != len(contribs):
            # If we had feature_names shorter/longer, try to reuse column names
            try:
                if feature_names and len(feature_names) < len(contribs):
                    # extend with generic suffixes
                    feature_names = feature_names + [f'f{i}' for i in range(len(feature_names), len(contribs))]
                else:
                    feature_names = [f'f{i}' for i in range(len(contribs))]
            except Exception:
                feature_names = [f'f{i}' for i in range(len(contribs))]

        feature_contribs = [
            {"feature": f, "shap_value": s}
            for f, s in zip(feature_names, contribs)
        ]

        feature_contribs_sorted = sorted(feature_contribs, key=lambda x: abs(x['shap_value']), reverse=True)

        base_value = None
        try:
            bv = sv.base_values
            if hasattr(bv, '__len__'):
                base_value = float(bv[0])
            else:
                base_value = float(bv)
        except Exception:
            base_value = None

        return {
            'base_value': base_value,
            'top_features': feature_contribs_sorted[:5],
            'all_features': feature_contribs_sorted
        }

    except Exception as e:
        return {'error': str(e)}
