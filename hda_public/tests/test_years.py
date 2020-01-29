from django.test import TestCase
from hda_privileged.models import Data_Set, Health_Indicator
from hda_public.queries import dataSetYearsForIndicator

class SampleGetYearsTest(TestCase):
    def setUp(self):
        self.h1 = Health_Indicator(name = 'Obisity')
        self.h1.save()

    #Determine if the number of items in the database for obesity is one
    def test_that_number_of_year_count_for_obisity_is_one_returned(self):
        Data_Set.objects.create(indicator=self.h1, year = 2014)
        years = dataSetYearsForIndicator('Obisity')
        self.assertEqual(len(years), 1)

    def test_if_the_current_year_in_the_database_for_obisity_is_2014(self):
        Data_Set.objects.create(indicator=self.h1, year = 2014)
        years = dataSetYearsForIndicator('Obisity')
        self.assertEqual(years, [2014])

    def test_that_one_kpi_can_have_multiple_years(self):
        Data_Set.objects.create(indicator=self.h1, year = 2014)
        Data_Set.objects.create(indicator=self.h1, year = 2017)
        Data_Set.objects.create(indicator=self.h1, year = 2016)
        Data_Set.objects.create(indicator=self.h1, year = 2018)
        years = dataSetYearsForIndicator('Obisity')
        self.assertEqual(len(years), 4)

    def test_that_the_years_are_returned_sorted_in_asc_order(self):
        Data_Set.objects.create(indicator=self.h1, year = 2014)
        Data_Set.objects.create(indicator=self.h1, year = 2017)
        Data_Set.objects.create(indicator=self.h1, year = 2016)
        Data_Set.objects.create(indicator=self.h1, year = 2018)
        years = dataSetYearsForIndicator('Obisity')
        self.assertEqual(years, [2014, 2016, 2017, 2018])
