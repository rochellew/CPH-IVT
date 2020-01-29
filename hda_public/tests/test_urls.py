from io import StringIO

from django.test import TestCase
from django.core.management import call_command


class HappyUrlsTestCase(TestCase):

    # setUpTestData runs once for the class, not once per test,
    # so we can load a data set one time to speed things up IF
    # we have multiple test methods and we don't need to reset
    @classmethod
    def setUpTestData(cls):
        out = StringIO()
        call_command('load_random_data_set', stdout=out)

    def testPublicUrlsLoad(self):
        paths_to_test = [
            ('home', ''),
            ('chart', '/chart/1?state=al'),
            ('select state', '/select'),
            ('select county', '/select/AL'),
            ('show state', '/state/AL'),
            ('show county', '/county/AL/001'),
        ]
        for (name, path) in paths_to_test:
            with self.subTest(label=name):
                response = self.client.get(path, follow=True)
                self.assertEqual(response.status_code, 200, response.content)
