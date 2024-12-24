from app2 import app

def test_valid_polynomial():
    client = app.test_client()
    response = client.post('/process_polynomial_new', json={
        "expression": "x2 + 2x",
        "userId": "8"
    })
    data = response.get_json()

    assert response.status_code == 200
    assert data['simplifiedExpression'] == 'x(x + 2)'
    assert data['factoredExpression'] == 'x(x + 2)'
    assert -2.0 in data['roots']

def test_invalid_polynomial():
    client = app.test_client()
    response = client.post('/process_polynomial_new', json={
        "expression": "",
        "userId": "456"
    })
    data = response.get_json()

    assert response.status_code == 400
    assert 'Veuillez fournir une expression' in data['error']

def test_missing_userId():
    client = app.test_client()
    response = client.post('/process_polynomial_new', json={
        "expression": "x^2 - 4"
    })
    data = response.get_json()

    assert response.status_code == 400
    assert 'userId est requis' in data['error']
