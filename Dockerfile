# Utilisation d'une image légère de Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .

# Installer les dépendances nécessaires
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copier l'ensemble de l'application
COPY . .

# Exposer le port 5001 pour Flask
EXPOSE 5001

# Lancer l'application
CMD ["python", "app2.py"]
