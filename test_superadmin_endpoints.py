import unittest
import json
from web_app import app


class TestSuperAdmin(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

    def test_superadmin_page(self):
        """Prueba que el endpoint /superadmin responda."""
        response = self.app.get("/superadmin")
        # Puede redirigir al login si no hay sesión,
        # pero verificamos que al menos no de un 404.
        self.assertNotEqual(response.status_code, 404)
        print(f"Status /superadmin: {response.status_code}")

    def test_api_resumen(self):
        """Prueba que el API de resumen de superadmin funcione."""
        with self.app.session_transaction() as sess:
            sess["web_user"] = {
                "rol": "rector",
                "documento": "rector1",
                "nombre": "Rector Prueba",
            }
        response = self.app.get("/api/superadmin/resumen")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("stats", data)
        self.assertIn("fases", data)
        print("API Resumen validado correctamente.")


if __name__ == "__main__":
    unittest.main()
