from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import PasswordResetCode, Sale, Stock

# Tests run with DEBUG=False, where the manifest storage needs `collectstatic`.
# Plain static storage keeps the tests independent of that build step.
TEST_SETTINGS = dict(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    # The test client speaks plain HTTP; production's HTTPS redirect would answer every request with 301.
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)

PASSWORD = 'Str0ng-test-passphrase'


@override_settings(**TEST_SETTINGS)
class MerkTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.member = User.objects.create_user('member', 'member@example.com', PASSWORD)
        self.staff = User.objects.create_user('staffer', 'staff@example.com', PASSWORD, is_staff=True)
        self.product = Stock.objects.create(
            product_name='Demo cement', product_description='50 kg bag', unit_cost=30000,
            unit_price=35000, quantity=12, product_supplier='Demo Supplies Ltd',
        )


class AuthPagesTests(MerkTestCase):
    def test_login_page_renders(self):
        response = self.client.get(reverse('home:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_login_succeeds_and_redirects_to_sales(self):
        response = self.client.post(reverse('home:login'), {'username': 'member', 'password': PASSWORD})
        self.assertRedirects(response, reverse('home:view_sales'))

    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse('home:login'), {'username': 'member', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_pages_require_login(self):
        for name in ['home:view_sales', 'home:products', 'home:add_sale', 'home:add_product', 'home:users_list']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn(reverse('home:login'), response['Location'])

    def test_signup_creates_account_and_sends_to_sign_in(self):
        response = self.client.post(reverse('home:signup'), {
            'username': 'newperson', 'email': 'new@example.com',
            'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('home:login'))
        self.assertTrue(User.objects.filter(username='newperson').exists())

    def test_logout_requires_post_and_signs_out(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('home:logout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have been logged out')
        self.assertEqual(self.client.get(reverse('home:view_sales')).status_code, 302)


class SalesAndProductsTests(MerkTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.member)

    def sale_data(self, **overrides):
        data = {
            'product_name': self.product.pk, 'unit_price': 35000, 'quantity': 2,
            'sales_agent': 'Demo Agent', 'customer_name': 'Demo Customer',
            'organization': '', 'customer_phonenumber': '', 'payment_method': 'Cash',
        }
        data.update(overrides)
        return data

    def test_sales_overview_shows_summary_and_records(self):
        Sale.objects.create(product_name=self.product, unit_price=35000, quantity=2,
                            sales_agent='Demo Agent', customer_name='Demo Customer')
        response = self.client.get(reverse('home:view_sales'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_sales'], 70000)
        self.assertEqual(response.context['todays_sales'], 1)
        self.assertEqual(response.context['units_in_stock'], 12)
        self.assertContains(response, 'Demo Customer')
        self.assertContains(response, '70,000')

    def test_add_edit_delete_sale(self):
        response = self.client.post(reverse('home:add_sale'), self.sale_data())
        self.assertRedirects(response, reverse('home:view_sales'))
        sale = Sale.objects.get()
        self.assertEqual(sale.total, 70000)

        response = self.client.post(reverse('home:edit_sale', args=[sale.pk]), self.sale_data(quantity=3))
        self.assertRedirects(response, reverse('home:view_sales'))
        sale.refresh_from_db()
        self.assertEqual(sale.quantity, 3)

        self.client.get(reverse('home:delete_sale', args=[sale.pk]))  # GET must not delete
        self.assertTrue(Sale.objects.filter(pk=sale.pk).exists())
        self.client.post(reverse('home:delete_sale', args=[sale.pk]))
        self.assertFalse(Sale.objects.filter(pk=sale.pk).exists())

    def test_negative_quantity_is_rejected(self):
        response = self.client.post(reverse('home:add_sale'), self.sale_data(quantity=-1))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quantity cannot be negative')
        self.assertFalse(Sale.objects.exists())

    def test_product_crud(self):
        response = self.client.post(reverse('home:add_product'), {
            'product_name': 'Demo paint', 'product_description': '20 L tin', 'unit_cost': 80000,
            'unit_price': 95000, 'quantity': 4, 'product_supplier': 'Demo Paints',
        })
        self.assertRedirects(response, reverse('home:products'))
        product = Stock.objects.get(product_name='Demo paint')

        page = self.client.get(reverse('home:products'))
        self.assertContains(page, 'Demo paint')

        response = self.client.get(reverse('home:edit_product', args=[product.pk]))
        self.assertContains(response, 'Edit Demo paint')
        self.client.post(reverse('home:delete_product', args=[product.pk]))
        self.assertFalse(Stock.objects.filter(pk=product.pk).exists())


class UserManagementPermissionTests(MerkTestCase):
    def test_member_cannot_see_or_change_other_users(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('home:users_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('home:edit_user', args=[self.staff.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('home:profile', args=[self.staff.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('home:delete_user', args=[self.staff.pk])).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    def test_member_cannot_make_themselves_staff(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('home:edit_user', args=[self.member.pk]), {
            'username': 'member', 'email': 'member@example.com', 'first_name': '', 'last_name': '',
            'is_active': 'on', 'is_staff': 'on',
        })
        self.assertEqual(response.status_code, 403)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_staff)

    def test_member_can_view_and_edit_own_profile(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('home:profile', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('home:profile', args=[self.member.pk]), {
            'first_name': 'Demo', 'last_name': 'Member', 'email': 'member@example.com', 'phone_number': '', 'bio': '',
        })
        self.assertRedirects(response, reverse('home:profile', args=[self.member.pk]))
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Demo')

    def test_staff_can_manage_users(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('home:users_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('home:profile', args=[self.member.pk])).status_code, 200)
        self.client.post(reverse('home:delete_user', args=[self.member.pk]))
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())

    def test_staff_cannot_delete_own_account(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('home:delete_user', args=[self.staff.pk]))
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    def test_users_link_hidden_from_members(self):
        users_link = f'href="{reverse("home:users_list")}"'
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(reverse('home:view_sales')), users_link)
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('home:view_sales')), users_link)


class PasswordResetTests(MerkTestCase):
    def request_code(self, email):
        return self.client.post(reverse('home:request_code'), {'email': email})

    def latest_code(self, email):
        return PasswordResetCode.objects.filter(email=email).latest('created_at')

    def test_same_response_for_unknown_email(self):
        known = self.request_code('member@example.com')
        unknown = self.request_code('nobody@example.com')
        message = 'If an account uses that email, we have sent it a 6-digit code.'
        self.assertContains(known, message)
        self.assertContains(unknown, message)
        self.assertFalse(PasswordResetCode.objects.filter(email='nobody@example.com').exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_full_reset_flow(self):
        self.request_code('member@example.com')
        code = self.latest_code('member@example.com').code
        response = self.client.post(reverse('home:verify_code'), {'email': 'member@example.com', 'code': code})
        self.assertRedirects(response, reverse('home:set_new_password'))
        new_password = 'An0ther-strong-passphrase'
        response = self.client.post(reverse('home:set_new_password'), {'password1': new_password, 'password2': new_password})
        self.assertRedirects(response, reverse('home:view_sales'))
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(new_password))

    def test_new_code_cancels_older_codes(self):
        self.request_code('member@example.com')
        first = self.latest_code('member@example.com')
        self.request_code('member@example.com')
        first.refresh_from_db()
        self.assertTrue(first.used)
        response = self.client.post(reverse('home:verify_code'), {'email': 'member@example.com', 'code': first.code})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid or expired code.')

    def test_expired_code_is_rejected(self):
        self.request_code('member@example.com')
        record = self.latest_code('member@example.com')
        record.expires_at = timezone.now() - timedelta(seconds=1)
        record.save()
        response = self.client.post(reverse('home:verify_code'), {'email': 'member@example.com', 'code': record.code})
        self.assertContains(response, 'Invalid or expired code.')

    def test_too_many_wrong_codes_cancels_code(self):
        self.request_code('member@example.com')
        record = self.latest_code('member@example.com')
        wrong = '000000' if record.code != '000000' else '111111'
        for _ in range(5):
            response = self.client.post(reverse('home:verify_code'), {'email': 'member@example.com', 'code': wrong})
        self.assertRedirects(response, reverse('home:request_code'))
        record.refresh_from_db()
        self.assertTrue(record.used)
        # The correct code no longer works either.
        response = self.client.post(reverse('home:verify_code'), {'email': 'member@example.com', 'code': record.code})
        self.assertRedirects(response, reverse('home:request_code'))

    def test_code_requests_are_limited(self):
        for _ in range(5):
            self.request_code('member@example.com')
        self.assertEqual(PasswordResetCode.objects.filter(email='member@example.com').count(), 3)
        self.assertEqual(len(mail.outbox), 3)

    def test_set_password_requires_verified_code(self):
        response = self.client.get(reverse('home:set_new_password'))
        self.assertRedirects(response, reverse('home:request_code'))
