from io import StringIO

from django.test import TestCase
from django.core.management import call_command

from hda_privileged.models import Data_Set, Data_Point, Health_Indicator, US_County
import hda_privileged.management.commands.load_random_data_set as lrds

class LoadRandomDataSetTestCase(TestCase):
    def setUp(self):
        self.outstr = StringIO()

    def test_custom_indicator_name(self):
        name = '"Test Me 5432"'
        before_count = Health_Indicator.objects.filter(name=name).count()

        call_command(
            'load_random_data_set',
            f'--indicator={name}',
            stdout=self.outstr)

        q = Health_Indicator.objects.filter(name=name)
        self.assertTrue(q.exists())
        self.assertEqual(q.count(), before_count + 1)

    def test_custom_ds_year(self):
        name = '"Test Me 3452"'
        year = 1492
        call_command(
            'load_random_data_set',
            f'--indicator={name}',
            f'--year={year}',
            stdout=self.outstr)

        hi = Health_Indicator.objects.get(name=name)
        ds = hi.data_sets.filter(year=year)
        self.assertTrue(ds.exists())
        self.assertTrue(ds.first().data_points.count() > 0)

    def test_custom_point_count(self):
        name = "tk421"
        size = 20

        call_command(
            'load_random_data_set',
            f'--count={size}',
            indicator=name,
            stdout=self.outstr)

        ds = Data_Set.objects.get(indicator__name=name)
        self.assertEqual(ds.data_points.count(), size)

    def test_default_point_count(self):
        name="tk421"

        call_command(
            'load_random_data_set',
            indicator=name,
            stdout=self.outstr)

        ds = Data_Set.objects.get(indicator__name=name)
        self.assertEqual(ds.data_points.count(), US_County.objects.count())
