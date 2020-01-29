import csv
import tempfile
import unittest

from django.test import TestCase

from hda_privileged.models import (
    Health_Indicator,
    Data_Set,
    Data_Point
)

from hda_privileged.upload_reading import (
    CHOICE_1FIPS,
    CHOICE_2FIPS,
    CHOICE_NAME,
    get_county_with_1fips,
    get_county_with_2fips,
    get_county_with_name,
    read_data_points_from_file
)


class CountyReaderTestCase(TestCase):

    # if you specify CHOICE_NAME, this should return a function Dict -> County
    # that queries the database using state and county names from the dict
    def test_name_choice(self):
        cases = [
            {'fips': '53069', 'State': 'Washington', 'County': 'Wahkiakum'},
            {'fips': '53069', 'State': 'Washington', 'County': 'Wahkiakum County'},
            {'fips': '72111', 'State': 'Puerto Rico', 'County': 'Peñuelas'},
            {'fips': '72111', 'State': 'Puerto Rico', 'County': 'Peñuelas Municipio'},
            {'fips': '13061', 'State': 'Georgia', 'County': 'Clay'},
            {'fips': '13063', 'State': 'Georgia', 'County': 'Clayton'},
        ]
        reader = get_county_with_name
        for case in cases:
            id = case['State'] + " + " + case['County']
            with self.subTest(county=id):
                (county, _) = reader(case)
                fips = county.state.fips + county.fips
                self.assertEqual(fips, case['fips'])

    # if you specify CHOICE_1FIPS, the function should use the 'FIPS' column
    def test_fips_choice(self):
        cases = [
            {'FIPS': '06037', 'State': 'California', 'sfips': '06', 'cfips': '037', 'County': 'Los Angeles County'},
            {'FIPS': '72033', 'State': 'Puerto Rico', 'sfips': '72', 'cfips': '033', 'County': 'Cataño Municipio'},
            {'FIPS': '01001', 'State': 'Alabama', 'sfips': '01', 'cfips': '001', 'County': 'Autauga County'},
        ]
        reader = get_county_with_1fips
        for case in cases:
            id = "{} + {}".format(case['State'], case['County'])
            with self.subTest(id=id):
                (county, _) = reader(case)
                self.assertEqual(county.state.fips, case['sfips'])
                self.assertEqual(county.fips, case['cfips'])
                self.assertEqual(county.name, case['County'])

    # if you specify CHOICE_2FIPS, the function should use the 'State' and 'County'
    # columns, but interpret them as partial FIPS codes
    def test_two_fips_choice(self):
        cases = [
            {'FIPS': '06037', 'State': '06', 'County': '037', 'sname': 'California', 'cname': 'Los Angeles County'},
            {'FIPS': '72033', 'State': '72', 'County': '033', 'sname': 'Puerto Rico', 'cname': 'Cataño Municipio'},
            {'FIPS': '01001', 'State': '01', 'County': '001', 'sname': 'Alabama', 'cname': 'Autauga County'},
        ]
        reader = get_county_with_2fips
        for case in cases:
            id = "{} + {}".format(case['sname'], case['cname'])
            with self.subTest(id=id):
                (county, _) = reader(case)
                fips = county.state.fips + county.fips
                self.assertEqual(fips, case['FIPS'])
                self.assertEqual(county.name, case['cname'])

    # this should explode - I'm including it because this spelling is how CHR
    # specifies this county, and I'm not sure how to handle that yet.
    @unittest.expectedFailure
    def test_LaSalle(self):
        reader = get_county_with_name
        row = {'State': 'Louisiana', 'County': 'La Salle'}
        (county, _) = reader(row)
        fips = county.state.fips + county.fips
        self.assertEqual(fips, '22059')

    def test_bad_county_name(self):
        reader = get_county_with_name
        row = {'State': 'Virginia', 'County': 'Not a county'}
        # 29 Jan 2019 - reader changed from throwing exceptions for
        # unmatched counties, to returning tulpes w/ errors
        (county, error) = reader(row)
        self.assertIsNone(county)
        self.assertIsNotNone(error)

    def test_bad_state_name(self):
        reader = get_county_with_name
        row = {'State': 'Not a state', 'County': 'Washington'}
        # 29 Jan 2019 - reader changed from throwing exceptions for
        # unmatched counties, to returning tuples w/ errors
        (county, error) = reader(row)
        self.assertIsNone(county)
        self.assertIsNotNone(error)


# these are happy path tests
# TODO: test failures!
class ReadDataPointsFromFileTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        hi = Health_Indicator.objects.create(name='Test Indicator')
        ds = Data_Set.objects.create(indicator=hi, year=2900)
        # will be available in methods as self.test_data_set
        cls.test_data_set = ds

    def setUp(self):
        # so in-memory changes to the data set do not persist between test methods
        self.test_data_set.refresh_from_db()

    def test_name_scheme(self):
        rows = [
            ('State', 'County', 'Value'),
            ('Virginia', 'Washington', '50.1'),
            ('Tennessee', 'Washington', '60.2'),
            ('Puerto Rico', 'Mayagüez Municipio', '70.3'),
        ]
        self.run_test_scheme(rows, CHOICE_NAME)

    def test_single_fips_scheme(self):
        rows = [
            ('FIPS', 'Value'),
            ('47179', '1.0'),
            ('72097', '2.0'),
        ]
        self.run_test_scheme(rows, CHOICE_1FIPS)

    def test_two_fips_scheme(self):
        rows = [
            ('State', 'County', 'Value'),
            ('47', '179', '2.0'),
            ('72', '097', '2.0'),
        ]
        self.run_test_scheme(rows, CHOICE_2FIPS)

    def run_test_scheme(self, rows, scheme):
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerows(rows)
            fp.seek(0)

            successful, unsuccessful = read_data_points_from_file(fp, scheme, self.test_data_set)

            # check that the points have NOT been saved
            self.assertFalse(Data_Point.objects.all().exists())
            # check that we have as many data points as we had rows
            self.assertEqual(len(successful), len(rows) - 1)
            # check that at least the first data point has the data set we specified
            self.assertEqual(successful[0].data_set, self.test_data_set)
            # check that the type of the value is float
            self.assertIsInstance(successful[0].value, float)

    def file_reading_harness(self, rows, scheme, assertions):
        '''If you find yourself writing the same test structure over and over again:
        1. Write some sample rows to a temporary file
        2. Read the rows back using read_data_points_from_file
        3. Make assertions on the results of (2)
        ...then this function is for you!
        It does exactly as stated - just give it the rows to use, the column schema
        to use when reading the points back, and a function containing your assertions.
        '''
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8', newline='') as tf:
            # setup the file contents
            writer = csv.writer(tf)
            writer.writerows(rows)
            tf.seek(0)

            # read data points out of the file with function under test
            data_points, errors = read_data_points_from_file(tf, scheme, self.test_data_set)

            # execute function containing assertions,
            # passing in the results of running the function under test
            assertions(data_points, errors)

    def test_unmatched_county_name(self):
        rows = [
            ['State', 'County', 'Value'],
            ['Virginia', 'Montgomery', '0.1'],
            ['Virginia', 'Roanoke', '0.2'],
            ['Virginia', 'Withevill', '0.3'],  # should not match!
        ]

        def asserts(data_points, errors):
            # check that we have the right number of each result
            self.assertEqual(len(data_points), 2)
            self.assertEqual(len(errors), 1)
            # check that the types of the results are what we expect
            self.assertIsInstance(data_points[0], Data_Point)
            self.assertIsInstance(errors, dict)

        self.file_reading_harness(rows, CHOICE_NAME, asserts)

    def test_unmatched_fips(self):
        rows = [
            ['FIPS', 'Value'],
            ['01001', '0.5'],  # is matched
            ['00000', '0.5'],  # is not matched
        ]

        def asserts(matched, unmatched):
            # should have two matched counties, one unmatched county
            self.assertEqual(len(matched), 1)
            self.assertEqual(len(unmatched), 1)
            # the objects in the matched list are data points,
            # the objects in the unmatched list are strings (error messages)
            self.assertIsInstance(matched[0], Data_Point)
            self.assertIsInstance(unmatched, dict)

        self.file_reading_harness(rows, CHOICE_1FIPS, asserts)
