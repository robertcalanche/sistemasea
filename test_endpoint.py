import requests
import json
import sys

# To test the endpoint, we'll try to use requests assuming the server is NOT running,
# but since the task says "crear un test mínimo... usando requests y ejecutarlo",
# it implies testing a live endpoint. However, if the server is not running, 
# it won't work.
# Alternatively, I can use the Werkzeug test client if I can import the app.
# Since importing web_app.py fails due to NameError: app, I'll try to find where 'app' is first defined.

print("Intentando probar el endpoint /api/superadmin/resumen...")

try:
    from web_app import app
    client = app.test_client()
    response = client.get('/api/superadmin/resumen')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.data)
        if 'stats' in data and 'fases' in data:
            print("TEST PASSED: Endpoint responds with 200 and contient expected keys.")
        else:
            print("TEST FAILED: Missing 'stats' or 'fases' in response.")
    else:
        print(f"TEST FAILED: Status code {response.status_code}")
except NameError as e:
    print(f"Error de importación: {e}. Parece que web_app.py usa 'app' antes de definirlo.")
except Exception as e:
    print(f"Error inesperado: {e}")
