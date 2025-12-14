"""
XAI helpers using SHAP to compute per-feature contributions for a prediction.
Version améliorée avec mapping correct des features.
"""
import pandas as pd
from typing import Any, Dict, List, Tuple
import shap
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import lime
import lime.lime_tabular
from app_module.config.settings import Config


def _get_original_feature_mapping(preprocessor: ColumnTransformer, input_cols: List[str]) -> Dict[int, str]:
    """
    Crée un mapping entre les indices des features transformées et les noms des features originales.
    Utilise get_feature_names_out() si disponible pour une meilleure précision.
    """
    mapping = {}
    
    if not hasattr(preprocessor, 'transformers_'):
        return {i: col for i, col in enumerate(input_cols)}
    
    # Essayer d'abord d'utiliser get_feature_names_out() qui est plus fiable
    try:
        transformed_names = preprocessor.get_feature_names_out(input_cols)
        
        # Parser les noms transformés pour extraire les noms originaux
        for idx, transformed_name in enumerate(transformed_names):
            # Format typique: "transformer__feature" ou "transformer__feature_value"
            parts = str(transformed_name).split('__')
            
            if len(parts) >= 2:
                # Le dernier élément contient souvent le nom original ou une valeur
                last_part = parts[-1]
                
                # Chercher la colonne originale correspondante
                found = False
                for col in input_cols:
                    # Vérifier si le nom de la colonne est dans le nom transformé
                    if col in transformed_name or col == last_part:
                        mapping[idx] = col
                        found = True
                        break
                
                if not found:
                    # Si on ne trouve pas, utiliser le dernier élément comme nom
                    mapping[idx] = last_part
            else:
                # Format simple, utiliser tel quel
                mapping[idx] = transformed_name
    except:
        # Fallback: méthode manuelle
        idx = 0
        for name, transformer, cols in preprocessor.transformers_:
            if transformer == 'drop':
                continue
            
            if not hasattr(cols, '__iter__') or isinstance(cols, str):
                cols = [cols] if isinstance(cols, str) else list(cols)
            
            # Pour les transformers qui produisent une feature par colonne d'entrée
            if name in ['binary', 'ordinal', 'scale']:
                for col in cols:
                    if col in input_cols:
                        mapping[idx] = col
                        idx += 1
            
            # Pour OneHotEncoder
            elif name == 'onehot':
                for col in cols:
                    if col in input_cols:
                        try:
                            if hasattr(transformer, 'categories_'):
                                col_idx = cols.index(col)
                                n_categories = len(transformer.categories_[col_idx])
                            else:
                                n_categories = 5  # Fallback pour Race
                            
                            for _ in range(n_categories):
                                mapping[idx] = col
                                idx += 1
                        except:
                            for _ in range(5):
                                mapping[idx] = col
                                idx += 1
            
            # Pour les autres transformers
            else:
                try:
                    if hasattr(transformer, 'get_feature_names_out'):
                        out_names = transformer.get_feature_names_out(cols)
                        for out_name in out_names:
                            # Chercher la colonne originale
                            for col in cols:
                                if col in str(out_name) and col in input_cols:
                                    mapping[idx] = col
                                    break
                            else:
                                mapping[idx] = str(out_name)
                            idx += 1
                    else:
                        for col in cols:
                            if col in input_cols:
                                mapping[idx] = col
                                idx += 1
                except:
                    for col in cols:
                        if col in input_cols:
                            mapping[idx] = col
                            idx += 1
    
    return mapping


def _aggregate_shap_by_original_features(shap_values: np.ndarray, mapping: Dict[int, str]) -> Dict[str, float]:
    """
    Agrège les valeurs SHAP par feature originale.
    Pour les features one-hot, on prend la somme des valeurs absolues pour montrer l'impact total.
    """
    aggregated = {}
    
    # Grouper les indices par feature originale
    feature_groups = {}
    for idx, feature_name in mapping.items():
        if idx < len(shap_values):  # S'assurer que l'index est valide
            if feature_name not in feature_groups:
                feature_groups[feature_name] = []
            feature_groups[feature_name].append(idx)
    
    # Agrégation
    for feature_name, indices in feature_groups.items():
        # Filtrer les indices valides
        valid_indices = [idx for idx in indices if 0 <= idx < len(shap_values)]
        
        if len(valid_indices) == 0:
            aggregated[feature_name] = 0.0
        elif len(valid_indices) == 1:
            # Feature simple: prendre la valeur directement
            aggregated[feature_name] = float(shap_values[valid_indices[0]])
        else:
            # Feature avec plusieurs valeurs (one-hot probablement)
            # On prend la somme des valeurs absolues pour montrer l'impact total de la feature
            # Cela permet d'agréger toutes les catégories one-hot en une seule importance
            values = shap_values[np.array(valid_indices)]
            aggregated[feature_name] = float(np.sum(np.abs(values)))
    
    return aggregated


def explain_model_prediction(model: Any, df_input: pd.DataFrame, n_background: int = 200) -> Dict[str, Any]:
    """
    Retourne les contributions SHAP pour une prédiction.
    Version améliorée avec mapping correct des features originales.
    """
    try:
        # ------------------------------------------------------------
        # 1) CHARGEMENT DU BACKGROUND DATASET (plus représentatif)
        # ------------------------------------------------------------
        try:
            df_full = pd.read_csv(Config.DATASET_PATH)
            
            # S'assurer que toutes les colonnes nécessaires sont présentes
            required_cols = list(df_input.columns)
            missing_cols = [c for c in required_cols if c not in df_full.columns]
            
            if missing_cols:
                # Utiliser df_input comme fallback
                bg = df_input.copy()
            else:
                # Sélectionner uniquement les colonnes nécessaires
                bg = df_full[required_cols].copy()
                
                # Échantillonnage stratifié si possible (pour avoir des exemples représentatifs)
                if bg.shape[0] > n_background:
                    bg = bg.sample(n=min(n_background, bg.shape[0]), random_state=42)
            
            # S'assurer que l'ordre des colonnes correspond
            bg = bg[df_input.columns]
            
        except Exception as e:
            # Fallback: utiliser df_input
            bg = df_input.copy()
            if bg.shape[0] > 1:
                bg = pd.concat([bg] * 10, ignore_index=True)  # Dupliquer pour avoir plus de données
        
        # ------------------------------------------------------------
        # 2) EXTRACTION DU PIPELINE
        # ------------------------------------------------------------
        clf = model
        preprocess = None
        
        if isinstance(model, Pipeline):
            preprocess = model.named_steps.get("preprocess", None)
            clf = model.named_steps.get("clf", model)
        
        # ------------------------------------------------------------
        # 3) TRANSFORMATION DES DONNÉES
        # ------------------------------------------------------------
        if preprocess is not None:
            try:
                bg_trans = preprocess.transform(bg)
                input_trans = preprocess.transform(df_input)
                
                # Créer le mapping features transformées -> originales
                feature_mapping = _get_original_feature_mapping(preprocess, list(df_input.columns))
                
            except Exception as e:
                # Fallback: pas de preprocessing
                bg_trans = bg.values
                input_trans = df_input.values
                feature_mapping = {i: col for i, col in enumerate(df_input.columns)}
        else:
            bg_trans = bg.values
            input_trans = df_input.values
            feature_mapping = {i: col for i, col in enumerate(df_input.columns)}
        
        # Convertir en array numpy si nécessaire
        if hasattr(bg_trans, 'toarray'):  # sparse matrix
            bg_trans = bg_trans.toarray()
        if hasattr(input_trans, 'toarray'):
            input_trans = input_trans.toarray()
        
        bg_trans = np.asarray(bg_trans)
        input_trans = np.asarray(input_trans)
        
        # ------------------------------------------------------------
        # 4) SÉLECTION DU BON EXPLAINER SHAP
        # ------------------------------------------------------------
        tree_types = (RandomForestClassifier, GradientBoostingClassifier,
                      HistGradientBoostingClassifier, DecisionTreeClassifier)
        is_tree = isinstance(clf, tree_types)
        
        # Fonction wrapper pour predict_proba (classe positive)
        def model_predict_proba(x):
            """Wrapper pour obtenir la probabilité de la classe positive"""
            x_array = np.asarray(x)
            
            # Si les données sont déjà transformées (on utilise directement le classifier)
            # car SHAP travaille avec les données transformées
            try:
                proba = clf.predict_proba(x_array)
            except:
                # Si ça échoue, essayer avec le pipeline complet
                if isinstance(model, Pipeline) and preprocess is None:
                    try:
                        if x_array.ndim == 1:
                            x_df = pd.DataFrame([x_array], columns=df_input.columns)
                        else:
                            x_df = pd.DataFrame(x_array, columns=df_input.columns)
                        proba = model.predict_proba(x_df)
                    except:
                        proba = clf.predict_proba(x_array)
                else:
                    proba = clf.predict_proba(x_array)
            
            # Retourner la probabilité de la classe positive (index 1)
            if proba.ndim == 2 and proba.shape[1] > 1:
                return proba[:, 1]
            return proba.flatten()
        
        # Créer l'explainer
        if is_tree:
            # Pour les modèles tree, utiliser TreeExplainer (plus rapide et exact)
            try:
                explainer = shap.TreeExplainer(clf, feature_perturbation="interventional")
                shap_values_obj = explainer(input_trans)
            except:
                # Fallback: utiliser le background dataset
                try:
                    explainer = shap.TreeExplainer(clf, bg_trans[:100], feature_perturbation="interventional")
                    shap_values_obj = explainer(input_trans)
                except:
                    # Dernier fallback: Explainer générique
                    explainer = shap.Explainer(model_predict_proba, bg_trans[:100])
                    shap_values_obj = explainer(input_trans)
        else:
            # Pour les autres modèles, utiliser Explainer avec background
            explainer = shap.Explainer(model_predict_proba, bg_trans[:100])
            shap_values_obj = explainer(input_trans)
        
        # ------------------------------------------------------------
        # 5) EXTRACTION DES VALEURS SHAP
        # ------------------------------------------------------------
        shap_values = shap_values_obj.values
        
        # Gérer les différentes dimensions
        if shap_values.ndim == 3:
            # (n_samples, n_classes, n_features)
            # Pour classification binaire, prendre la classe positive (index 1)
            try:
                if hasattr(clf, 'classes_'):
                    pos_idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 1
                else:
                    pos_idx = 1 if shap_values.shape[1] > 1 else 0
                shap_vals = shap_values[0, pos_idx, :]
            except:
                shap_vals = shap_values[0, 1, :] if shap_values.shape[1] > 1 else shap_values[0, 0, :]
        elif shap_values.ndim == 2:
            # (n_samples, n_features) ou (n_features, n_samples)
            if shap_values.shape[0] == 1:
                shap_vals = shap_values[0, :]
            else:
                shap_vals = shap_values[:, 0]
        else:
            shap_vals = shap_values.flatten()
        
        # S'assurer que c'est un array 1D
        shap_vals = np.asarray(shap_vals).flatten()
        
        # ------------------------------------------------------------
        # 6) AGRÉGATION PAR FEATURE ORIGINALE
        # ------------------------------------------------------------
        aggregated_shap = _aggregate_shap_by_original_features(shap_vals, feature_mapping)
        
        # Créer la liste des contributions
        feature_contribs = [
            {"feature": feature, "shap_value": float(value)}
            for feature, value in aggregated_shap.items()
        ]
        
        # Trier par valeur absolue décroissante
        feature_contribs_sorted = sorted(
            feature_contribs, 
            key=lambda x: abs(x["shap_value"]), 
            reverse=True
        )
        
        # ------------------------------------------------------------
        # 7) BASE VALUE
        # ------------------------------------------------------------
        try:
            if hasattr(shap_values_obj, 'base_values'):
                base_vals = shap_values_obj.base_values
                if isinstance(base_vals, np.ndarray):
                    if base_vals.ndim > 1:
                        # Prendre la valeur pour la classe positive
                        base_value = float(base_vals[0, 1] if base_vals.shape[1] > 1 else base_vals[0, 0])
                    else:
                        base_value = float(base_vals[0])
                else:
                    base_value = float(base_vals)
            else:
                base_value = None
        except:
            base_value = None
        
        return {
            "base_value": base_value,
            "top_features": feature_contribs_sorted[:10],  # Top 10 au lieu de 5
            "all_features": feature_contribs_sorted
        }
    
    except Exception as e:
        import traceback
        return {"error": f"Erreur SHAP: {str(e)}\n{traceback.format_exc()}"}


def explain_model_prediction_lime(model: Any, df_input: pd.DataFrame, n_samples: int = 5000) -> Dict[str, Any]:
    """
    Retourne les contributions LIME pour une prédiction.
    """
    try:
        # 1) CHARGEMENT DU TRAIN SET (LIME a besoin de stats sur le training set)
        try:
            df_full = pd.read_csv(Config.DATASET_PATH)
            # S'assurer que les colonnes correspondent
            train_data = df_full[df_input.columns]
        except:
            # Fallback
            train_data = df_input.copy() # Très mauvais pour LIME mais évite le crash

        # 2) GESTION DU PIPELINE ET PREPROCESSING
        # LIME a besoin de travailler sur des arrays numpy si c'est un modèle sklearn standard,
        # ou on peut lui passer le pipeline complet s'il gère les colonnes brutes.
        # Ici nos pipelines gèrent les DataFrames bruts via 'preprocess'.
        
        # On va utiliser LIME sur les données BRUTES (avant preprocessing)
        # car c'est plus interprétable pour l'utilisateur.
        
        # Convertir les colonnes catégorielles en indices pour LIME (si besoin) ou laisser LIME gérer
        # LimeTabularExplainer gère les catégorielles si on lui dit lesquelles c'est.
        
        categorical_features = []
        categorical_names = {}
        for idx, col in enumerate(train_data.columns):
            if train_data[col].dtype == 'object':
                categorical_features.append(idx)
                # On doit encoder les valeurs pour LIME
                # Pour simplifier ici, on va laisser LIME se débrouiller ou
                # convertir temporairement en label encoding pour fit l'explainer
                pass

        # NOTE: LIME est complexe à setup parfaitement avec des pipelines complexes.
        # Approche simplifiée: On passe le train_data tel quel, mais LIME attend du numpy souvent.
        
        # Convert to numpy for LIME
        train_data_np = train_data.values
        input_np = df_input.values[0]

        # Fonction de prédiction probabiliste custom
        def predict_proba_fn(arr):
            # arr est un numpy array de (n_samples, n_features)
            # Reconvertir en DataFrame pour le pipeline
            df = pd.DataFrame(arr, columns=df_input.columns)
            
            # Restaurer les types (LIME convertit souvent en float)
            # Ceci est critique car le pipeline attend des strings pour les catégorielles
            for col in df_input.columns:
                if df_input[col].dtype == 'object':
                     # Essayer de mapper les floats vers les valeurs originales si on avait encodé...
                     # C'est là que ça coince souvent.
                     # Simplification: SI le pipeline plante sur des types, on a un souci.
                     pass
            
            return model.predict_proba(df)

        # Pour faire fonctionner LIME proprement avec des features string/catégorielles sans prise de tête:
        # On va créer un explainer qui 'apprend' sur le training set brut.
        # MAIS LimeTabularExplainer attend que les catégorielles soient des entiers.
        
        # ==> STRATÉGIE ROBUSTE:
        # Encoder les strings en entiers pour LIME, et décoder dans la predict_fn.
        
        transformers = {} # col_idx -> LabelEncoder
        from sklearn.preprocessing import LabelEncoder
        
        train_encoded = train_data.copy()
        
        for idx, col in enumerate(train_data.columns):
            if train_data[col].dtype == 'object':
                le = LabelEncoder()
                # Fit sur train + input pour être sûr d'avoir toutes les classes
                combined = pd.concat([train_data[col], df_input[col]])
                le.fit(combined.astype(str))
                
                train_encoded[col] = le.transform(train_data[col].astype(str))
                transformers[idx] = le
            
        # Créer l'explainer
        explainer = lime.lime_tabular.LimeTabularExplainer(
            train_encoded.values,
            feature_names=list(train_data.columns),
            class_names=['Sain', 'Risque'],
            categorical_features=list(transformers.keys()),
            mode='classification',
            discretize_continuous=True
        )

        # Encoder l'input
        input_encoded = df_input.copy()
        for idx, le in transformers.items():
            name = df_input.columns[idx]
            input_encoded[name] = le.transform(df_input[name].astype(str))
            
        # Wrapper de prédiction qui décode
        def custom_predict(np_array):
            # np_array: shape (n, n_features) ints/floats
            df_temp = pd.DataFrame(np_array, columns=train_data.columns)
            
            # Décoder
            for idx, le in transformers.items():
                name = train_data.columns[idx]
                # LIME perturbe en float, on arrondi
                vals = df_temp[name].round().astype(int)
                # Clip pour éviter erreurs d'index
                vals = vals.clip(0, len(le.classes_) - 1)
                df_temp[name] = le.inverse_transform(vals)
                
            return model.predict_proba(df_temp)

        # Expliquer
        exp = explainer.explain_instance(
            input_encoded.values[0],
            custom_predict,
            num_features=10,
            num_samples=n_samples
        )
        
        # Formater
        c = exp.as_list()
        # c est [(feature_cond, contribution), ...]
        
        structured = []
        for feature_name, value in c:
            structured.append({
                "feature": feature_name,
                "value": float(value),
                "is_risk": value > 0
            })
            
        return {"explanation": structured}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Erreur LIME: {str(e)}"}
