from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Empleado


class RutasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Empleado.objects.create_superuser(
            nombre_usuario="admin_test",
            email="admin_test@example.com",
            password="Passw0rd!123",
            nombres="Admin",
            apellidos="Test",
        )

    def test_root_anonimo_redirige_a_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_pagina_login_carga(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión")

    def test_dashboard_con_usuario_autenticado(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel principal")

    def test_listas_principales(self):
        self.client.force_login(self.user)

        urls = [
            "patients:list",
            "doctors:list",
            "exams:list",
            "results:list",
        ]

        for name in urls:
            response = self.client.get(reverse(name))
            self.assertEqual(
                response.status_code,
                200,
                f"La URL {name} debía responder 200",
            )

    def test_formulario_paciente_carga(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("patients:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nuevo paciente")
