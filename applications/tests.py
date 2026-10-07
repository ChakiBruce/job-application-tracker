from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse

from .models import Application


class ApplicationWebTests(TestCase):
    def form_data(self, **changes):
        values = dict(company="東京, Tech", role="Engineer", application_date="2026-10-07", status="Applied")
        values.update(changes)
        return values

    def test_empty_list_and_add_page(self):
        response = self.client.get(reverse("applications:list"))
        self.assertContains(response, "Start your application list")
        self.assertContains(self.client.get(reverse("applications:create")), "csrfmiddlewaretoken")

    def test_form_saves_redirects_and_refresh_does_not_duplicate(self):
        response = self.client.post(reverse("applications:create"), self.form_data(), follow=True)
        self.assertRedirects(response, reverse("applications:list"))
        self.assertContains(response, "東京, Tech")
        self.assertContains(response, "Application saved.")
        self.client.get(reverse("applications:list"))
        self.assertEqual(Application.objects.count(), 1)
        with connection.cursor() as cursor:
            cursor.execute("SELECT company, application_date FROM applications")
            company, applied = cursor.fetchone()
        self.assertEqual(company, "東京, Tech")
        self.assertEqual(str(applied), "2026-10-07")

    def test_invalid_form_does_not_save_and_preserves_values(self):
        for changes in ({"company": "   "}, {"role": ""}, {"status": ""}, {"application_date": "2026-02-30"}):
            with self.subTest(changes=changes):
                response = self.client.post(reverse("applications:create"), self.form_data(**changes))
                self.assertContains(response, "Please check the fields below.")
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(response.context["form"]["application_date"].value(), changes.get("application_date", "2026-10-07"))
        self.assertEqual(Application.objects.count(), 0)

    def test_existing_terminal_record_is_visible(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO applications (company, role, application_date, status) VALUES (%s, %s, %s, %s)",
                ["Existing company", "Developer", "2026-10-06", "Interviewing"],
            )
        response = self.client.get(reverse("applications:list"))
        self.assertContains(response, "Existing company")
        self.assertContains(response, "Interviewing")

    def test_user_html_is_escaped(self):
        response = self.client.post(reverse("applications:create"), self.form_data(company="<script>alert(1)</script>"), follow=True)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>")

    def test_post_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("applications:create"), self.form_data()).status_code, 403)
        client.get(reverse("applications:create"))
        data = self.form_data(csrfmiddlewaretoken=client.cookies["csrftoken"].value)
        self.assertEqual(client.post(reverse("applications:create"), data).status_code, 302)

    def test_list_rejects_post(self):
        self.assertEqual(self.client.post(reverse("applications:list")).status_code, 405)
