from flask import Flask, request, jsonify
from flask_cors import CORS  # Importer CORS
import re
from sympy import symbols, sympify, diff, factor
import numpy as np
import requests

app = Flask(_name_)

# Activer CORS pour toutes les routes
CORS(app)  # Cela autorise toutes les origines, mais vous pouvez être plus spécifique si nécessaire.

# Variable symbolique pour le polynôme
x = symbols('x')

def normalize_expression(expr):
    expr = re.sub(r'x(\d+)', r'x^\1', expr)
    expr = expr.replace('x^', 'x**')
    expr = re.sub(r'(?<=\d)(x)', r'*x', expr)
    expr = re.sub(r'(?<=\d)(\()', r'*(', expr)
    expr = re.sub(r'([a-zA-Z0-9])\+', r'\1 +', expr)
    expr = re.sub(r'(\+|\-)\s*', r' \1 ', expr)
    expr = expr.replace('**1', ' ')
    return expr

def format_simplified_expression(expr):
    expr_str = str(expr)
    expr_str = expr_str.replace('**', '')
    expr_str = re.sub(r'(\d)(x\*)', r'\1x', expr_str)
    expr_str = re.sub(r'\*', '', expr_str)
    expr_str = expr_str.replace('x^1', 'x')
    expr_str = re.sub(r'(\+|\-)1x', r'\1x', expr_str)
    return expr_str

def newton_raphson_roots(expr, guess=0.0, tolerance=1e-7, max_iter=1000):
    f = sympify(expr)
    f_prime = diff(f, x)
    current_guess = guess
    for _ in range(max_iter):
        f_val = f.subs(x, current_guess)
        f_prime_val = f_prime.subs(x, current_guess)
        if abs(f_val) < tolerance:
            return float(current_guess)
        if f_prime_val == 0:
            break
        current_guess = current_guess - f_val / f_prime_val
    return None

SPRING_BOOT_API_URL = "http://localhost:8082/api/store-polynomial"  # URL de l'API Spring Boot

@app.route('/process_polynomial_new', methods=['POST'])
def process_polynomial_new():
    data = request.get_json()
    expression = data.get("expression", "")

    if not expression:
        return jsonify({"error": "Veuillez fournir une expression de polynôme."}), 400

    normalized_expr = normalize_expression(expression)

    try:
        # Simplification du polynôme
        simplified_expr = sympify(normalized_expr).simplify()
        simplified_str = format_simplified_expression(simplified_expr)

        # Factorisation du polynôme
        factored_expr = factor(simplified_expr)
        factored_str = format_simplified_expression(factored_expr)

        # Résolution des racines par Newton-Raphson
        roots = []
        guesses = np.linspace(-10, 10, 50)  # Génération de points initiaux
        for guess in guesses:
            root = newton_raphson_roots(simplified_expr, guess)
            if root is not None and not any(abs(root - r) < 1e-5 for r in roots):
                roots.append(root)

        result = {
            "simplifiedExpression": simplified_str,
            "factoredExpression": factored_str,
            "roots": [round(r, 5) for r in roots]
        }

        # Envoi des résultats à l'API Spring Boot
        response = requests.post(SPRING_BOOT_API_URL, json=result)
        if response.status_code == 200:
            return jsonify(result), 200
        else:
            return jsonify({"error": "Erreur lors de l'enregistrement dans Spring Boot."}), response.status_code

    except Exception as e:
        return jsonify({"error": f"Erreur lors du traitement : {str(e)}"}), 400

if _name_ == '_main_':
    app.run(debug=True, port=5001)