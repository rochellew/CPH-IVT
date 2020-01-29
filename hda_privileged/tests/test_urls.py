from io import StringIO

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model


class HappyUrlsTestCase(TestCase):

    @classmethod
    def funcname(cls):
        # load a data set
        out = StringIO()
        call_command('load_random_data_set', stdout=out)
        # create a user that we can log in with
        User = get_user_model()
        cls.user = User.objects.create_user(username='testuser', password='12345')

    def testPrivUrlsLoad(self):
        # list of (name, path) to test
        # TODO: if this app is tested in isolation, this will fail
        # because the project root URLConf defines the 'priv' portion
        # of the path; should be using this:
        # https://docs.djangoproject.com/en/2.1/topics/testing/tools/#urlconf-configuration
        paths_to_test = [
            ('home', '/priv/home'),
            ('home filtered', '/priv/home/1'),
            ('upload', '/priv/upload'),
            ('create indicator', '/priv/indicator/add'),
            ('login', '/priv/login'),
        ]
        # log in first
        self.client.login(username='testuser', password='12345')
        # check each of these URLs
        for (name, path) in paths_to_test:
            with self.subTest(label=name):
                response = self.client.get(path, follow=True)
                self.assertEqual(response.status_code, 200, response.content)

    def testLogin(self):
        response = self.client.post(
            '/priv/login/',
            {'username': 'testuser', 'password': '12345'}
        )
        self.assertEqual(response.status_code, 200)

    # ToDO: test logout
    # ToDO: test that URLs are not publicly accessible!
    def testLogout(self):
        response = self.client.get('/priv/logout/')
        self.assertRedirects(response, '/priv/login/')

    def testPrivUrlsNotPublic(self):
        paths = [
            '/priv/home/',
            '/priv/home/1/',
            '/priv/indicator/add/',
            '/priv/upload/',
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, follow=True)
                self.assertRedirects(response, f'/priv/login/?next={path}')
