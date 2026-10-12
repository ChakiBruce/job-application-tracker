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
        for changes in ({"company": "   "}, {"role": ""}, {"status": ""}, {"status": "Unknown"}, {"application_date": "2026-02-30"}):
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


    def test_add_status_dropdown_defaults_to_applied(self):
        response = self.client.get(reverse("applications:create"))
        self.assertContains(response, '<select name="status"')
        self.assertContains(response, '<option value="Applied" selected>Applied</option>', html=True)
        for status in ("Interviewing", "Offer", "Rejected"):
            self.assertContains(response, f'<option value="{status}">{status}</option>', html=True)
        self.assertNotContains(response, "<datalist")

    def test_add_accepts_each_selectable_status(self):
        for status in ("Applied", "Interviewing", "Offer", "Rejected"):
            with self.subTest(status=status):
                response = self.client.post(reverse("applications:create"), self.form_data(status=status))
                self.assertRedirects(response, reverse("applications:list"))
                self.assertEqual(Application.objects.latest("pk").status, status)
        self.assertEqual(Application.objects.count(), 4)

class ApplicationStatusTests(TestCase):
    def setUp(self):
        self.application = Application.objects.create(
            company="Example", role="Engineer", application_date="2026-10-12", status="Applied",
        )
        self.other = Application.objects.create(
            company="Other", role="Developer", application_date="2026-10-11", status="Offer",
        )
        self.url = reverse("applications:update_status", args=[self.application.pk])

    def test_list_links_to_selected_application_and_get_prefills_status(self):
        self.assertContains(self.client.get(reverse("applications:list")), f'href="{self.url}"')
        response = self.client.get(self.url)
        self.assertEqual(response.context["form"]["status"].value(), "Applied")
        self.assertContains(response, "Example")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Applied")

    def test_update_persists_and_leaves_other_fields_and_records_unchanged(self):
        fields = ["company", "role", "application_date"]
        before = Application.objects.values(*fields).get(pk=self.application.pk)
        response = self.client.post(self.url, {
            "status": "Interviewing", "company": "Unwanted change", "role": "Changed",
        }, follow=True)
        self.assertRedirects(response, reverse("applications:list"))
        self.assertContains(response, "Application status updated.")
        self.application.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.application.status, "Interviewing")
        self.assertEqual(self.other.status, "Offer")
        self.assertEqual(Application.objects.values(*fields).get(pk=self.application.pk), before)
        self.assertEqual(Application.objects.count(), 2)
        self.assertContains(Client().get(reverse("applications:list")), "Interviewing")

    def test_invalid_status_keeps_saved_status(self):
        for status in ("", "   ", "Unknown", "x" * 101):
            with self.subTest(status=status):
                response = self.client.post(self.url, {"status": status})
                self.assertContains(response, "Please check the status below.")
                self.assertTrue(response.context["form"].errors)
                self.application.refresh_from_db()
                self.assertEqual(self.application.status, "Applied")

    def test_missing_application_returns_404(self):
        url = reverse("applications:update_status", args=[self.other.pk + 1])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"status": "Rejected"}).status_code, 404)

    def test_update_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url, {"status": "Rejected"}).status_code, 403)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Applied")
        client.get(self.url)
        response = client.post(self.url, {
            "status": "Rejected", "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "Rejected")

    def test_unsupported_method_is_rejected(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)

    def test_status_is_a_dropdown_with_current_value_selected(self):
        response = self.client.get(self.url)
        self.assertContains(response, '<select name="status"')
        self.assertContains(response, '<option value="Applied" selected>Applied</option>', html=True)
        for status in ("Interviewing", "Offer", "Rejected"):
            self.assertContains(response, f'<option value="{status}">{status}</option>', html=True)
        self.assertNotContains(response, "<datalist")

    def test_all_dropdown_statuses_can_be_saved(self):
        for status in ("Applied", "Interviewing", "Offer", "Rejected"):
            with self.subTest(status=status):
                self.assertRedirects(self.client.post(self.url, {"status": status}), reverse("applications:list"))
                self.application.refresh_from_db()
                self.assertEqual(self.application.status, status)


class ApplicationSortingTests(TestCase):
    def setUp(self):
        self.zeta = Application.objects.create(
            company="Zeta", role="Zulu", application_date="2026-10-01", status="Offer",
        )
        self.alpha = Application.objects.create(
            company="Alpha", role="Beta", application_date="2026-10-12", status="Applied",
        )
        self.lower_alpha = Application.objects.create(
            company="alpha", role="alpha", application_date="2026-10-12", status="Interviewing",
        )
        self.url = reverse("applications:list")

    def test_default_is_newest_first_with_stable_date_ties(self):
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["applications"]), [self.alpha, self.lower_alpha, self.zeta])
        self.assertEqual(response.context["selected_sort"], "date_desc")

    def test_each_sort_option_orders_applications(self):
        a, b, c = self.zeta, self.alpha, self.lower_alpha
        expected_orders = {
            "date_desc": [b, c, a], "date_asc": [a, b, c],
            "company_asc": [b, c, a], "company_desc": [a, b, c],
            "role_asc": [c, b, a], "role_desc": [a, b, c],
            "status_asc": [b, c, a], "status_desc": [a, c, b],
        }
        for sort, expected in expected_orders.items():
            with self.subTest(sort=sort):
                response = self.client.get(self.url, {"sort": sort})
                self.assertEqual(list(response.context["applications"]), expected)
                self.assertEqual(response.context["selected_sort"], sort)

    def test_unknown_sort_falls_back_to_newest(self):
        for sort in ("", "missing", "company; DROP TABLE applications", "company__unknown"):
            with self.subTest(sort=sort):
                response = self.client.get(self.url, {"sort": sort})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected_sort"], "date_desc")
                self.assertEqual(list(response.context["applications"]), [self.alpha, self.lower_alpha, self.zeta])

    def test_selected_sort_is_rendered_and_ids_are_hidden(self):
        response = self.client.get(self.url, {"sort": "company_asc"})
        self.assertContains(response, '<option value="company_asc" selected>Company: A–Z</option>', html=True)
        self.assertNotContains(response, '<th scope="col">ID</th>', html=True)
        self.assertNotContains(response, f"<td>{self.zeta.pk}</td>", html=True)
        self.assertContains(response, f'href="{reverse("applications:update_status", args=[self.zeta.pk])}"')

    def test_sorting_handles_empty_table(self):
        Application.objects.all().delete()
        response = self.client.get(self.url, {"sort": "role_desc"})
        self.assertContains(response, "Start your application list")
        self.assertEqual(list(response.context["applications"]), [])
