"""
Gestionnaire de base de données pour enregistrer les tests utilisateurs
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from app_module.config.settings import Config


def column_exists(cursor, table_name, column_name):
    """Vérifier si une colonne existe dans une table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns


class TestDatabase:
    """Gestionnaire de base de données pour les tests"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialiser la connexion à la base de données"""
        if db_path is None:
            db_path = os.path.join(Config.BASE_DIR, 'data', 'tests.db')
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.init_database()
        self.migrate_database()
    
    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialiser les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_used TEXT NOT NULL,
                prediction INTEGER NOT NULL,
                probability REAL NOT NULL,
                input_features TEXT NOT NULL,
                explanation TEXT,
                certificate_path TEXT,
                user_ip TEXT
            )
        ''')
        
        # Migration: Ajouter les colonnes manquantes si elles n'existent pas
        if not column_exists(cursor, 'tests', 'certificate_path'):
            try:
                cursor.execute('ALTER TABLE tests ADD COLUMN certificate_path TEXT')
                conn.commit()
                print("[DB] Colonne certificate_path ajoutée")
            except sqlite3.OperationalError as e:
                print(f"[DB] Erreur ajout colonne certificate_path: {e}")
        
        if not column_exists(cursor, 'tests', 'user_ip'):
            try:
                cursor.execute('ALTER TABLE tests ADD COLUMN user_ip TEXT')
                conn.commit()
                print("[DB] Colonne user_ip ajoutée")
            except sqlite3.OperationalError as e:
                print(f"[DB] Erreur ajout colonne user_ip: {e}")
        
        conn.commit()
        conn.close()
    
    def migrate_database(self):
        """Migrer la base de données pour ajouter les colonnes manquantes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Migration: Ajouter les colonnes manquantes si elles n'existent pas
        if not column_exists(cursor, 'tests', 'certificate_path'):
            try:
                cursor.execute('ALTER TABLE tests ADD COLUMN certificate_path TEXT')
                conn.commit()
                print("[DB] Colonne certificate_path ajoutée")
            except sqlite3.OperationalError as e:
                print(f"[DB] Erreur ajout colonne certificate_path: {e}")
        
        if not column_exists(cursor, 'tests', 'user_ip'):
            try:
                cursor.execute('ALTER TABLE tests ADD COLUMN user_ip TEXT')
                conn.commit()
                print("[DB] Colonne user_ip ajoutée")
            except sqlite3.OperationalError as e:
                print(f"[DB] Erreur ajout colonne user_ip: {e}")
        
        conn.close()
    
    def save_test(
        self,
        model_used: str,
        prediction: int,
        probability: float,
        input_features: Dict[str, Any],
        explanation: Optional[Dict[str, Any]] = None,
        certificate_path: Optional[str] = None,
        user_ip: Optional[str] = None
    ) -> int:
        """Sauvegarder un test dans la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tests 
            (model_used, prediction, probability, input_features, explanation, certificate_path, user_ip)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            model_used,
            prediction,
            probability,
            json.dumps(input_features),
            json.dumps(explanation) if explanation else None,
            certificate_path,
            user_ip
        ))
        
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return test_id
    
    def get_all_tests(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupérer tous les tests avec pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tests
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        tests = []
        for row in rows:
            test = dict(row)
            test['input_features'] = json.loads(test['input_features'])
            if test['explanation']:
                test['explanation'] = json.loads(test['explanation'])
            tests.append(test)
        
        return tests
    
    def get_test_by_id(self, test_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un test par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tests WHERE id = ?', (test_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            test = dict(row)
            test['input_features'] = json.loads(test['input_features'])
            if test['explanation']:
                test['explanation'] = json.loads(test['explanation'])
            return test
        
        return None
    
    def get_test_count(self) -> int:
        """Obtenir le nombre total de tests"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM tests')
        result = cursor.fetchone()
        conn.close()
        
        return result['count'] if result else 0


# Instance globale
db = TestDatabase()

