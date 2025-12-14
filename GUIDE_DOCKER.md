# Guide Complet - SkinCheck avec Docker

## 📋 Prérequis

### 1. Installer Docker
```bash
# Mettre à jour le système
sudo apt update

# Installer Docker
sudo apt install docker.io -y

# Démarrer Docker
sudo systemctl start docker
sudo systemctl enable docker

# Vérifier l'installation
docker --version
```

### 2. Installer Docker Compose
```bash
# Installer Docker Compose
sudo apt install docker-compose -y

# Vérifier l'installation
docker-compose --version
```

### 3. Ajouter votre utilisateur au groupe Docker (optionnel)
```bash
# Pour éviter d'utiliser sudo à chaque fois
sudo usermod -aG docker $USER

# Redémarrer la session ou exécuter
newgrp docker

# Tester sans sudo
docker ps
```

## 🚀 Démarrage de l'Application

### Étape 1 : Se placer dans le dossier du projet
```bash
cd /home/sebabte/canc
```

### Étape 2 : Construire l'image Docker
```bash
# Première fois ou après modification du code
docker-compose build

# Avec cache désactivé (si problèmes)
docker-compose build --no-cache
```

### Étape 3 : Démarrer l'application
```bash
# Démarrer en arrière-plan
docker-compose up -d

# Ou démarrer avec les logs visibles
docker-compose up
```

### Étape 4 : Vérifier que l'application fonctionne
```bash
# Voir les conteneurs actifs
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### Étape 5 : Accéder à l'application
Ouvrez votre navigateur et allez sur :
```
http://localhost:5000
```

## 🛠️ Commandes Utiles

### Gestion du Conteneur
```bash
# Arrêter l'application
docker-compose down

# Redémarrer l'application
docker-compose restart

# Arrêter et supprimer tout (conteneurs, réseaux, volumes)
docker-compose down -v

# Voir les logs en temps réel
docker-compose logs -f web

# Voir les dernières 100 lignes de logs
docker-compose logs --tail=100 web
```

### Mise à Jour du Code
```bash
# Après avoir modifié le code
docker-compose down
docker-compose build
docker-compose up -d
```

### Accéder au Shell du Conteneur
```bash
# Ouvrir un terminal dans le conteneur
docker-compose exec web bash

# Ou avec docker directement
docker exec -it $(docker ps -q -f name=canc) bash
```

### Nettoyage
```bash
# Supprimer les images inutilisées
docker image prune -a

# Supprimer tous les conteneurs arrêtés
docker container prune

# Nettoyage complet du système Docker
docker system prune -a --volumes
```

## 📊 Utilisation de l'Application

### 1. Page d'Accueil
- Remplir le formulaire avec les données du patient
- Choisir le modèle de classification (Random Forest recommandé)
- Cliquer sur "Lancer l'Analyse"

### 2. Résultats
L'application affiche :
- **Badge de risque** : Vert (sain) ou Rouge (risque)
- **Probabilité** : Pourcentage de risque
- **Analyse SHAP** : Importance globale des facteurs
- **Analyse LIME** : Impact local des facteurs

### 3. Générer un Rapport PDF
- Cliquer sur "Télécharger le Rapport"
- Le PDF contient :
  - Données du patient
  - Résultat de l'analyse
  - Graphiques SHAP et LIME
  - Informations médicales de référence
  - Sources officielles

### 4. Autres Fonctionnalités
- **Analyse Image** : `/image-analysis/`
- **Dashboard** : `/dashboard/`
- **Administration** : `/admin/`

## 🔧 Dépannage

### Le port 5000 est déjà utilisé
Modifier `docker-compose.yml` :
```yaml
ports:
  - "8080:5000"  # Utiliser le port 8080
```
Puis accéder à `http://localhost:8080`

### L'application ne démarre pas
```bash
# Voir les logs d'erreur
docker-compose logs web

# Reconstruire sans cache
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Erreur "Cannot connect to Docker daemon"
```bash
# Démarrer Docker
sudo systemctl start docker

# Vérifier le statut
sudo systemctl status docker
```

### Problème de permissions
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Redémarrer la session
newgrp docker
```

### Les modèles ne se chargent pas
Vérifier que les fichiers `.pkl` sont présents :
```bash
ls -la models/
```

### Erreur de mémoire
Augmenter la mémoire allouée à Docker dans les paramètres Docker Desktop ou modifier `docker-compose.yml` :
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 4G
```

## 📝 Variables d'Environnement

Modifier `docker-compose.yml` pour ajouter des variables :
```yaml
environment:
  - XAI_MODE=legacy
  - FLASK_ENV=production
  - DEBUG=False
```

## 🔒 Production

### Recommandations pour la production :
1. **Utiliser un reverse proxy (nginx)**
2. **Activer HTTPS**
3. **Limiter les ressources** :
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```
4. **Sauvegarder les données** :
```yaml
volumes:
  - ./data:/app/data
  - ./models:/app/models
```

## 📞 Support

En cas de problème :
1. Vérifier les logs : `docker-compose logs -f`
2. Vérifier que Docker fonctionne : `docker ps`
3. Reconstruire l'image : `docker-compose build --no-cache`
4. Redémarrer : `docker-compose restart`

## 🎯 Résumé des Commandes Essentielles

```bash
# Démarrer l'application
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter l'application
docker-compose down

# Redémarrer après modification du code
docker-compose down && docker-compose build && docker-compose up -d

# Accéder à l'application
http://localhost:5000
```
