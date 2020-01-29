from django.test import TestCase
from django.core.management import call_command
from hda_public.queries import dataSetForYear
from hda_privileged.models import Health_Indicator, Data_Set

class SelectDataForYearTestCase(TestCase):

    # setUp runs once before each of the other test cases,
    # so we can use it to set up things that all of our test
    # cases will need.
    def setUp(self):
        # for instance, we'll probably want at least one health indicator to
        # exist, so we can use it when setting up our other tests.
        # By saving it as a property of "self", our other tests will be
        # able to access it as a property/attribute
        self.indicator_name = 'A Test Indicator'
        self.health_indicator = Health_Indicator(name=self.indicator_name)
        self.health_indicator.save()

    # Verify no datasets returned when none has been created
    def test_none_returned(self):
        name="Returned from empty sandbox"
        result = dataSetForYear(2018, self.indicator_name)
        self.assertIsNone(result)

    # 1. Set up the inputs/environment for the test
    # (in our case, this means creating things for the database)
    # 2. Perform the operation that we want to test (dataSetForYear)
    # 3. Check whether the results are what we expect (assert)
    def test_dataset_returned(self):
        name = "Dataset returned"
        # 1. add a data set to our sandbox database
        Data_Set.objects.create(indicator=self.health_indicator, year=2018)
        # 2. now try to retrieve it using our method
        # (For the current implementation of dataSetForYear, we must include an indicator name)
        setReturned = dataSetForYear(2018, self.indicator_name)
        # 3. check that we get what we expect - the QuerySet should have at least one result
        self.assertIsNotNone(setReturned)

    # This is a good test idea: make sure the year of the result matches the one you ask for
    def test_correct_year_returned(self):
        name = "Correct year returned"
        # set up data to test against
        Data_Set.objects.create(indicator=self.health_indicator, year=2018)
        Data_Set.objects.create(indicator=self.health_indicator, year=2017)
        correctYear = dataSetForYear(2018, self.indicator_name)
        # since the result is a QuerySet, we need to use .first() to extract the first object in the list of results
        self.assertEqual(correctYear.year, 2018)
