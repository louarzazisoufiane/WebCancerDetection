"""
Routes admin pour voir les tests enregistrés (protégé par mot de passe)
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from app_module.utils.database import db
import os
from app_module.config.settings import Config

# S'assurer que la base de données est initialisée
try:
    # Vérifier que db est bien initialisé
    if not hasattr(db, 'db_path'):
        from app_module.utils.database import TestDatabase
        db = TestDatabase()
except Exception as e:
    print(f"Erreur initialisation DB dans admin: {e}")

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Mot de passe admin simple (à changer en production)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')


def require_admin():
    """Vérifier que l'utilisateur est authentifié comme admin"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion admin"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.tests_list'))
        else:
            return render_template('admin_login.html', error='Mot de passe incorrect')
    
    return render_template('admin_login.html')


@admin_bp.route('/logout')
def admin_logout():
    """Déconnexion admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/')
@admin_bp.route('/tests')
def tests_list():
    """Page principale pour afficher tous les tests (admin seulement)"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # S'assurer que db est bien initialisé
        if not hasattr(db, 'get_all_tests'):
            from app_module.utils.database import TestDatabase
            db_instance = TestDatabase()
            tests = db_instance.get_all_tests(limit=per_page, offset=offset)
            total_count = db_instance.get_test_count()
        else:
            tests = db.get_all_tests(limit=per_page, offset=offset)
            total_count = db.get_test_count()
        
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return render_template(
            'admin_tests.html',
            tests=tests,
            current_page=page,
            total_pages=total_pages,
            total_count=total_count
        )
    except Exception as e:
        print(f"Erreur dans tests_list: {e}")
        import traceback
        traceback.print_exc()
        return render_template(
            'admin_tests.html',
            tests=[],
            current_page=1,
            total_pages=1,
            total_count=0
        )


@admin_bp.route('/test/<int:test_id>')
def test_detail(test_id):
    """Page de détail d'un test spécifique"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    test = db.get_test_by_id(test_id)
    
    if not test:
        return render_template('error.html', message='Test non trouvé'), 404
    
    return render_template('admin_test_detail.html', test=test)


@admin_bp.route('/certificates/<path:filename>')
def serve_certificate(filename):
    """Servir les certificats"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))
    
    cert_dir = os.path.join(Config.BASE_DIR, 'data', 'certificates')
    return send_from_directory(cert_dir, filename)

