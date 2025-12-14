"""
Routes pour le dashboard
"""
from flask import Blueprint
import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from app_module.config.settings import Config
from app_module.utils.data import load_dataset, get_value_options
from app_module.utils import get_logger

logger = get_logger(__name__)


def dashboard_bp(server):
    """Créer et enregistrer le dashboard Dash"""
    
    # Charger le dataset
    try:
        df = load_dataset(Config.DATASET_PATH)
        logger.info(f"Dataset chargé: {len(df)} lignes")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du dataset: {e}")
        df = pd.DataFrame()
    
    # Créer l'application Dash
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboard/",
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    
    # Personnalisation du style
    # Personnalisation du style (Template Maître)
    dash_app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>Dashboard | DermoIA Pro</title>
            {%favicon%}
            {%css%}
            <!-- Fonts -->
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <!-- Icons -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <!-- Main Style -->
            <link rel="stylesheet" href="/static/style.css">
            <style>
                /* Overrides specific to Dash/Bootstrap conflicts if any */
                .card {
                    margin-bottom: 0 !important; /* Let grid handle spacing */
                }
            </style>
        </head>
        <body>
            <div class="app-container">
                <header class="main-header">
                    <div class="brand">
                        <a href="/" class="brand-text" style="display: flex; align-items: center; gap: 0.75rem; text-decoration: none;">
                            <i class="fa-solid fa-chart-pie brand-icon"></i>
                            <div>
                                <h1>Dashboard Analytique</h1>
                                <p>Vue d'ensemble et performances</p>
                            </div>
                        </a>
                    </div>
                    <div class="header-actions">
                        <a href="/" class="btn btn-secondary"><i class="fa-solid fa-arrow-left"></i> Retour</a>
                        <a href="/dashboard/" class="btn btn-primary"><i class="fa-solid fa-rotate"></i> Actualiser</a>
                    </div>
                </header>
                
                {%app_entry%}
            </div>
            
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Layout
    dash_app.layout = dbc.Container([
        
        # Statistiques clés
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Icon
                    html.Div(html.I(className="fa-solid fa-users"), className="stat-icon", style={'background': 'var(--primary-light)', 'color': 'var(--primary-color)', 'marginBottom': '10px'}),
                    html.Div("Total Patients", style={'color': 'var(--neutral-500)', 'fontWeight': '600', 'textTransform': 'uppercase', 'fontSize': '0.9rem'}),
                    html.Div(id="stat-total", className="stat-value", style={'fontSize': '2rem', 'fontWeight': '700', 'color': 'var(--neutral-900)'}),
                ], className="card card-accent-primary", style={'textAlign': 'center', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            ], md=3, className="mb-3"),
            dbc.Col([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-triangle-exclamation"), className="stat-icon", style={'background': 'var(--danger-bg)', 'color': 'var(--danger-color)', 'marginBottom': '10px'}),
                    html.Div("Cas Cancer Peau", style={'color': 'var(--neutral-500)', 'fontWeight': '600', 'textTransform': 'uppercase', 'fontSize': '0.9rem'}),
                    html.Div(id="stat-cancer", className="stat-value", style={"color": "var(--danger-color)", 'fontSize': '2rem', 'fontWeight': '700'}),
                ], className="card card-accent-danger", style={'textAlign': 'center', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            ], md=3, className="mb-3"),
            dbc.Col([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-chart-line"), className="stat-icon", style={'background': 'var(--warning-bg)', 'color': 'var(--warning-color)', 'marginBottom': '10px'}),
                    html.Div("Taux d'Incidence", style={'color': 'var(--neutral-500)', 'fontWeight': '600', 'textTransform': 'uppercase', 'fontSize': '0.9rem'}),
                    html.Div(id="stat-rate", className="stat-value", style={"color": "var(--warning-text)", 'fontSize': '2rem', 'fontWeight': '700'}),
                ], className="card card-accent-warning", style={'textAlign': 'center', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            ], md=3, className="mb-3"),
            dbc.Col([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-weight-scale"), className="stat-icon", style={'background': 'var(--success-bg)', 'color': 'var(--success-color)', 'marginBottom': '10px'}),
                    html.Div("BMI Moyen", style={'color': 'var(--neutral-500)', 'fontWeight': '600', 'textTransform': 'uppercase', 'fontSize': '0.9rem'}),
                    html.Div(id="stat-bmi", className="stat-value", style={"color": "var(--success-text)", 'fontSize': '2rem', 'fontWeight': '700'}),
                ], className="card card-accent-success", style={'textAlign': 'center', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            ], md=3, className="mb-3"),
        ], className="mb-4"),
        
        # Filtres
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([html.I(className="fa-solid fa-filter me-2"), "Filtres Avancés"], style={'fontWeight': '700', 'color': 'var(--primary-dark)', 'background': 'transparent', 'borderBottom': '1px solid var(--neutral-200)'}),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Catégories d'Âge", className="fw-bold"),
                                dcc.Dropdown(
                                    id='age-filter',
                                    options=get_value_options(df, 'AgeCategory') if not df.empty else [{'label': 'Aucune donnée', 'value': None}],
                                    value=[],
                                    multi=True,
                                    placeholder='Sélectionnez les catégories d\'âge'
                                )
                            ], md=6, className="mb-3"),
                            dbc.Col([
                                dbc.Label("Statut Fumeur", className="fw-bold"),
                                dcc.Dropdown(
                                    id='smoking-filter',
                                    options=get_value_options(df, 'Smoking') if not df.empty else [{'label': 'Aucune donnée', 'value': None}],
                                    value=[],
                                    multi=True,
                                    placeholder='Sélectionnez le statut fumeur'
                                )
                            ], md=6, className="mb-3"),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Sexe", className="fw-bold"),
                                dcc.Dropdown(
                                    id='sex-filter',
                                    options=get_value_options(df, 'Sex') if not df.empty else [{'label': 'Aucune donnée', 'value': None}],
                                    value=[],
                                    multi=True,
                                    placeholder='Sélectionnez le sexe'
                                )
                            ], md=6),
                            dbc.Col([
                                dbc.Label("Activité Physique", className="fw-bold"),
                                dcc.Dropdown(
                                    id='activity-filter',
                                    options=get_value_options(df, 'PhysicalActivity') if not df.empty else [{'label': 'Aucune donnée', 'value': None}],
                                    value=[],
                                    multi=True,
                                    placeholder='Sélectionnez activité physique'
                                )
                            ], md=6),
                        ]),
                    ])
                ], className="card")
            ], width=12)
        ], className="mb-4"),
        
        # Graphiques - Ligne 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribution par Catégorie d'Âge", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='age-distribution', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribution BMI", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='bmi-distribution', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
        ]),
        
        # Graphiques - Ligne 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Statut Fumeur", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='smoking-distribution', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cas Cancer Peau", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='cancer-distribution', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
        ]),
        
        # Graphiques - Ligne 3
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("État de Santé Général", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='health-distribution', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Maladie Cardiaque vs Cancer", style={'fontWeight': '700'}),
                    dbc.CardBody(dcc.Graph(id='heart-cancer-chart', style={'height': '350px'}))
                ], className="card card-accent-primary")
            ], md=6, className="mb-4"),
        ]),
        
        # Résumé statistique
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Résumé Statistique", style={'fontWeight': '700', 'color': 'var(--primary-dark)'}),
                    dbc.CardBody(html.Div(id='stats-summary'))
                ], className="card")
            ], width=12, className="mb-4")
        ]),
        
    ], fluid=True, style={'padding': '0', 'backgroundColor': 'transparent'})
    
    # Callbacks
    @dash_app.callback(
        [Output('stat-total', 'children'),
         Output('stat-cancer', 'children'),
         Output('stat-rate', 'children'),
         Output('stat-bmi', 'children'),
         Output('age-distribution', 'figure'),
         Output('bmi-distribution', 'figure'),
         Output('smoking-distribution', 'figure'),
         Output('cancer-distribution', 'figure'),
         Output('health-distribution', 'figure'),
         Output('heart-cancer-chart', 'figure'),
         Output('stats-summary', 'children')],
        [Input('age-filter', 'value'),
         Input('smoking-filter', 'value'),
         Input('sex-filter', 'value'),
         Input('activity-filter', 'value')]
    )
    def update_dashboard(age_val, smoking_val, sex_val, activity_val):
        """Mettre à jour tous les graphiques selon les filtres"""
        
        if df.empty:
            empty_fig = {'data': [], 'layout': {'title': 'Pas de données'}}
            return '0', '0', '0%', '0', empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, dbc.Alert("Pas de données", color="warning")
        
        # Filtrer les données (support multi-select)
        filtered_df = df.copy()

        def _apply_filter(df_in, column, val):
            if val is None or val == []:
                return df_in
            # accept scalar or list
            if isinstance(val, str):
                if val == 'all':
                    return df_in
                return df_in[df_in[column] == val]
            try:
                # treat as iterable of choices
                if 'all' in val:
                    return df_in
            except Exception:
                pass
            return df_in[df_in[column].isin(val)]

        filtered_df = _apply_filter(filtered_df, 'AgeCategory', age_val)
        filtered_df = _apply_filter(filtered_df, 'Smoking', smoking_val)
        filtered_df = _apply_filter(filtered_df, 'Sex', sex_val)
        filtered_df = _apply_filter(filtered_df, 'PhysicalActivity', activity_val)
        
        # Statistiques
        total = len(filtered_df)
        # Compter les cas positifs en acceptant 'Yes'/'No' ou 1/0 ou True/False
        if 'SkinCancer' in filtered_df.columns:
            cancer_count = filtered_df['SkinCancer'].isin([1, 'Yes', 'yes', 'YES', True]).sum()
        else:
            cancer_count = 0
        rate = f"{(cancer_count/total*100):.1f}%" if total > 0 else "0%"
        bmi_avg = f"{filtered_df['BMI'].mean():.1f}"
        
        # Graphique Age
        age_fig = px.bar(
            filtered_df['AgeCategory'].value_counts().reset_index().rename(columns={'AgeCategory': 'Âge', 'count': 'Nombre'}),
            x='Âge', y='Nombre',
            color_discrete_sequence=['#0369a1'] # Primary
        )
        age_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
        
        # Graphique BMI
        bmi_fig = px.histogram(
            filtered_df,
            x='BMI',
            nbins=30,
            color_discrete_sequence=['#0d9488'] # Accent Teal
        )
        bmi_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
        
        # Graphique Smoking
        smoking_fig = px.pie(
            values=filtered_df['Smoking'].value_counts().values,
            names=filtered_df['Smoking'].value_counts().index,
            color_discrete_sequence=['#059669', '#dc2626'] # Success, Danger
        )
        smoking_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        
        # Graphique Cancer
        cancer_counts = [cancer_count, total - cancer_count]
        cancer_fig = px.pie(
            values=cancer_counts,
            names=['Positif', 'Négatif'],
            color_discrete_sequence=['#dc2626', '#059669'] # Danger, Success
        )
        cancer_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        
        # Graphique Santé
        health_cols = [col for col in filtered_df.columns if col.startswith('GenHealth_')]
        if health_cols:
            health_data = filtered_df[health_cols].sum()
            health_fig = px.bar(
                x=health_data.index.str.replace('GenHealth_', ''),
                y=health_data.values,
                color_discrete_sequence=['#0369a1']
            )
        else:
                # Utiliser la colonne brute si pas de colonnes OneHotEncoded
                health_fig = px.bar(
                    filtered_df['GenHealth'].value_counts().reset_index().rename(columns={'GenHealth': 'Santé', 'count': 'Nombre'}),
                    x='Santé', y='Nombre',
                    color_discrete_sequence=['#0369a1']
                )
        health_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title='État', yaxis_title='Nombre')
        
        # Graphique Heart Disease vs Cancer
        if 'SkinCancer' in filtered_df.columns:
            heart_cancer_data = filtered_df.groupby(['HeartDisease', 'SkinCancer']).size().unstack(fill_value=0)
            heart_fig = px.bar(
                heart_cancer_data,
                barmode='group',
                color_discrete_sequence=['#059669', '#dc2626']
            )
        else:
            heart_fig = {'data': [], 'layout': {'title': 'Pas de données'}}
        heart_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title='Maladie Cardiaque', yaxis_title='Nombre')
        
        # Résumé statistique
        summary = dbc.Row([
            dbc.Col([
                html.P([html.Strong("👥 Population: "), f"{total:,} patients"]),
                html.P([html.Strong("🏥 Cancer Peau: "), f"{cancer_count:,} cas ({rate})"]),
                html.P([html.Strong("⚖️ BMI Moyen: "), f"{bmi_avg}"]),
            ], md=4),
            dbc.Col([
                html.P([html.Strong("❤️ Maladie Cardiaque: "), f"{filtered_df['HeartDisease'].isin([1, 'Yes', True]).sum():,}" ]),
                html.P([html.Strong("🚬 Fumeurs: "), f"{filtered_df['Smoking'].isin([1, 'Yes', True]).sum():,}" ]),
                html.P([html.Strong("🏃 Activité Physique: "), f"{filtered_df['PhysicalActivity'].isin([1, 'Yes', True]).sum():,}" ]),
            ], md=4),
            dbc.Col([
                html.P([html.Strong("😴 Sommeil Moyen: "), f"{filtered_df['SleepTime'].mean():.1f}h"]),
                html.P([html.Strong("🧠 Santé Mentale: "), f"{filtered_df['MentalHealth'].mean():.1f} jours"]),
                html.P([html.Strong("💪 Santé Physique: "), f"{filtered_df['PhysicalHealth'].mean():.1f} jours"]),
            ], md=4),
        ])
        
        return f"{total:,}", f"{cancer_count:,}", rate, bmi_avg, age_fig, bmi_fig, smoking_fig, cancer_fig, health_fig, heart_fig, summary
    
    return dash_app
