from flask import Flask, request, jsonify
from flask_cors import CORS  # Importer CORS
import re
from sympy import symbols, sympify, diff, factor
import numpy as np
import requests

app = Flask(__name__)

# Activer CORS pour toutes les routes
CORS(app)  # Cela autorise toutes les origines, mais vous pouvez être plus spécifique si nécessaire.

# Variable symbolique pour le polynôme
x = symbols('x')

def normalize_expression(expr):
    # Remplacer 'x' suivi d'un chiffre par 'x**chiffre' pour la puissance
    expr = re.sub(r'(\d*)x(\d+)', r'\1*x**\2', expr)
    
    # Ajouter les multiplications manquantes entre un nombre et une variable
    expr = re.sub(r'(?<=\d)(x)', r'*\1', expr)
    expr = re.sub(r'(?<=\d)(\()', r'*\1', expr)
    
    # Supprimer les multiplications inutiles au début ou après des opérateurs
    expr = re.sub(r'(\+|\-)\s*\*', r'\1 ', expr)  # "* après + ou -" -> pas nécessaire
    expr = re.sub(r'^\*', '', expr)  # "* au début" -> pas nécessaire

    # Ajouter une constante +0 si elle est absente
    if not re.search(r'[+-]\s*\d', expr):  # Aucun terme constant trouvé
        expr += " + 0"

    return expr.strip()

def format_simplified_expression(expr):
    expr_str = str(expr)
    expr_str = expr_str.replace('**', '')
    expr_str = re.sub(r'(\d)(x\*)', r'\1x', expr_str)
    expr_str = re.sub(r'\*', '', expr_str)
    expr_str = expr_str.replace('x^1', 'x')
    expr_str = re.sub(r'(\+|\-)1x', r'\1x', expr_str)
    return expr_str

def newton_raphson_roots(expr, guess=0.0, tolerance=1e-7, max_iter=1000):
    try:
        f = sympify(expr)
        f_prime = diff(f, x)
        current_guess = guess
        for _ in range(max_iter):
            f_val = f.subs(x, current_guess)
            f_prime_val = f_prime.subs(x, current_guess)
            if abs(f_val) < tolerance:  # Si proche de zéro, c'est une racine
                return float(current_guess)
            if f_prime_val == 0:  # Eviter la division par zéro
                print(f"Dérivée nulle pour le guess {current_guess}")
                return None
            current_guess = current_guess - f_val / f_prime_val
        return None
    except Exception as e:
        print(f"Erreur dans Newton-Raphson : {e}")
        return None

SPRING_BOOT_API_URL = "http://localhost:8082/api/store-polynomial"  # URL de l'API Spring Boot

@app.route('/process_polynomial_new', methods=['POST'])
def process_polynomial_new():
    data = request.get_json()

    # Récupérer l'expression et l'userId depuis la requête
    expression = data.get("expression", "")
    user_id = data.get("userId", None)

    if not expression:
        return jsonify({"error": "Veuillez fournir une expression de polynôme."}), 400

    if not user_id:
        return jsonify({"error": "userId est requis."}), 400

    normalized_expr = normalize_expression(expression)
    print(f"Expression normalisée : {normalized_expr}")

    try:
        # Simplification du polynôme
        simplified_expr = sympify(normalized_expr).simplify()
        print(f"Expression simplifiée : {simplified_expr}")
        simplified_str = format_simplified_expression(simplified_expr)

        # Factorisation du polynôme
        factored_expr = factor(simplified_expr)
        print(f"Expression factorisée : {factored_expr}")
        factored_str = format_simplified_expression(factored_expr)

        # Résolution des racines par Newton-Raphson
        roots = []
        guesses = np.linspace(-10, 10, 50)  # Génération de points initiaux
        for guess in guesses:
            print(f"Newton-Raphson initial guess : {guess}")
            root = newton_raphson_roots(simplified_expr, guess)
            print(f"Résultat de Newton-Raphson pour {guess} : {root}")
            if root is not None and not any(abs(root - r) < 1e-5 for r in roots):
                roots.append(root)

        print(f"Racines trouvées : {roots}")

        # Construire les résultats
        result = {
            "simplifiedExpression": simplified_str,
            "factoredExpression": factored_str,
            "roots": [round(r, 5) for r in roots],
            "userId": user_id
        }

        print(f"Résultat à envoyer à Spring Boot : {result}")

        # Envoi des résultats à l'API Spring Boot
        response = requests.post(SPRING_BOOT_API_URL, json=result)
        print(f"Réponse Spring Boot : {response.status_code}, {response.text}")
        if response.status_code == 200:
            return jsonify(result), 200
        else:
            return jsonify({"error": "Erreur lors de l'enregistrement dans Spring Boot."}), response.status_code

    except Exception as e:
        print(f"Erreur détectée : {e}")
        return jsonify({"error": f"Erreur lors du traitement : {str(e)}"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)
