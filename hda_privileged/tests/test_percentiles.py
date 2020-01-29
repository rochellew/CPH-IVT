from django.test import TestCase
from hda_privileged.percentile import (
    PercentileBoundsError,
    rank,
    percentile,
    get_percentile_values,
    get_percentiles_for_points,
    assign_percentiles_to_points)
from functools import reduce


class RankCalculationTestCase(TestCase):

    # with N = 0, the first case of p in [0, 1/(n+1)] becomes
    # p in [0, 1] which is always true - so this should always
    # return 1 no matter what percentile is requested.
    def test_zero_sample_size(self):
        for p in range(1, 10):
            x = rank(p / 10, 0)
            self.assertEqual(x, 1)

    # with N = 1, the ranges become p in [0, 0.5] and p in [0.5, 1],
    # the second case whould never match, because its range is (0.5, 0.5).
    # (no values match this because the endpoints are both excluded and equal to each other.)
    # for values below 0.5, we should return 1, and for values above 0.5 we should return
    # sample_size - in this case the two are both 1, so the returned value should
    # always be 1 (again)
    def test_one_sample_size(self):
        for p in range(1, 100):
            with self.subTest(p=p):
                x = rank(p / 100, 1)
                self.assertEqual(x, 1)

    # our calculation method does not allow percentiles of 0% or 100%
    # *this makes sense* because no value in a list of values is greater than 100%
    # of the values in the list - this would imply that the maximum value
    # is greater than itself. Throw an exception if given p = 0 or p = 1
    def test_excluded_percentile(self):
        with self.assertRaises(PercentileBoundsError):
            rank(0, 100)

        with self.assertRaises(PercentileBoundsError):
            rank(1, 100)

    # the first case has an inclusive boundary at 1/N+1
    # for a sample size of 2, this is at 33%
    def test_lower_boundary(self):
        n = 2
        p1 = 0.333  # 33.3%
        p2 = 0.334  # 33.4%

        self.assertEqual(rank(p1, n), 1)
        # can't use assertEqual here b/c floating point numbers
        self.assertAlmostEqual(rank(p2, n), p2 * (n + 1))

    # the third case has an inclusive boundary at N/N+1
    # for a sample size of 4, this is at 80%
    def test_upper_boundary(self):
        n = 4
        p1 = 0.80  # 80%
        p2 = 0.799  # 79.9%

        # should trigger the 3rd case
        self.assertEqual(rank(p1, n), n)
        # should trigger the second case
        self.assertAlmostEqual(rank(p2, n), p2 * (n + 1))

    # the rank for the 2nd quartile / median should *always* be the "middle",
    #  regardless of sample size:
    # https://en.wikipedia.org/wiki/Percentile#Commonalities_between_the_variants_of_this_method
    def test_median(self):
        for n in range(1, 14):
            with self.subTest(size=n):
                x = rank(0.5, n)
                midpoint = (n + 1) / 2
                self.assertEqual(x, midpoint)


class PercentileCalculationTestCase(TestCase):

    # should throw an exception
    def test_empty_list(self):
        with self.assertRaises(PercentileBoundsError):
            percentile(0.5, [])

    # should always return the same value
    def test_singleton_list(self):
        v = 20
        single = [v]
        pl = [p / 100 for p in range(1, 100)]
        for p in pl:
            with self.subTest(p=p):
                self.assertEqual(percentile(p, single), v)

    # for percentiles <= 1/3, we should get the lower number
    # for percentiles >= 2/3, we should get the upper number
    # for anything else, we should get an interpolation
    def test_2_list(self):
        double = [1, 2]
        lower = 1/3
        upper = 2/3

        def get_expected(p):
            if p <= lower:
                return double[0]
            elif p >= upper:
                return double[1]
            else:
                # this should be the rank
                r = p * (len(double) + 1)
                # the calculated percentile should be interpolated between the upper and
                # lower values based on the fractional part of the rank
                f = r % 1
                return double[0] + f * (double[1] - double[0])

        for p in [p / 100 for p in range(1, 100)]:
            with self.subTest(p=p):
                result = percentile(p, double)
                expected = get_expected(p)
                self.assertEqual(result, expected)

    # for any list of values, p = 0.5 should return the "middle" value
    # (if the length is even, will be split)
    def test_median(self):
        for n in range(1, 15):
            vs = list(range(0, n))
            size = len(vs)
            m_index = (size - 1) // 2
            m_value = vs[m_index] if size % 2 != 0 else vs[m_index] + 0.5

            with self.subTest(n=n):
                self.assertEqual(percentile(0.5, vs), m_value)

    # if all the values are the same, then every percentile
    # should also be the same
    def test_identical_values(self):
        all_the_same = [42] * 10
        for p in [p / 10 for p in range(1, 10)]:
            with self.subTest(p=p):
                self.assertEqual(percentile(p, all_the_same), 42)

    # for 10 values, the edge cases are at <10% and >90%, so
    # percentages between those should be interpolated.
    # If all the values are 1 apart, then the amount interpolated will be the
    # same as the percentage itself
    def test_wide_interpolation(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ps = [p / 10 for p in range(1, 10)]

        for (i, p) in enumerate(ps):
            with self.subTest(p=p):
                self.assertAlmostEqual(percentile(p, values), values[i] + p)


class PercentileValuesTestCase(TestCase):

    def test_no_values(self):
        with self.assertRaises(PercentileBoundsError):
            get_percentile_values([0.5], [])

    def test_single_value(self):
        value = 5
        ps = [0.25, 0.75, 0.50]

        expected = [(p, percentile(p, [value])) for p in ps]

        # automaticall invokes assertListEqual
        self.assertEqual(expected, get_percentile_values(ps, [value]))


# https://stackoverflow.com/a/6192298
class MockPoint(object):
    def __init__(self, value, *, percentile=None):
        self.value = value
        self.rank = percentile

    def __eq__(self, other):
        if hasattr(other, 'value') and hasattr(other, 'percentile'):
            return self.value == other.value and self.rank == other.rank
        else:
            return False

    def __str__(self):
        return f"Point v:{self.value} p:{self.rank}"


# helper for checking if a list is sorted
# we could also copy the list, sort the copy, and use comparison,
# but that would take 2n + sort, this just takes n
def is_sorted(xs, *, key=lambda x: x):
    previous = None
    current = None

    for x in xs:
        current = key(x)
        if previous is not None:
            if previous > current:
                return False
        previous = current

    return True


# don't assume the helper function is correct
class IsSortedTest(TestCase):

    def test_is_sorted_empty(self):
        self.assertTrue(is_sorted([]))

    def test_is_sorted_singleton(self):
        self.assertTrue(is_sorted([42]))

    def test_is_sorted_two(self):
        self.assertTrue(is_sorted([2, 4]))

    def test_is_not_sorted_two(self):
        self.assertFalse(is_sorted([3, 2]))

    def test_is_sorted_same(self):
        self.assertTrue(is_sorted([3, 3, 3, 3, 3, 3]))

    def test_is_not_sorted(self):
        self.assertFalse(is_sorted([8, 4, 23, 16, 15, 42]))

    def test_is_sorted(self):
        self.assertTrue(is_sorted([4, 8, 15, 16, 23, 42]))

    def test_is_sorted_after_sort_in_place(self):
        values = [45, 7, 3, 1, 23, 18, 6, 6, 7, 4, 3, 1]
        self.assertFalse(is_sorted(values))
        values.sort()
        self.assertTrue(is_sorted(values))

    def test_is_sorted_with_key(self):
        structures = [
            (4, 3),
            (1, 2),
            (42, 23),
            (8, 8),
            (0, 1),
            (45, 5),
        ]

        def first(t): return t[0]

        def second(t): return t[1]

        # sort based on the second value
        structures.sort(key=second)
        self.assertFalse(is_sorted(structures, key=first))
        self.assertTrue(is_sorted(structures, key=second))

        # sort based on the first value
        structures.sort(key=first)
        self.assertFalse(is_sorted(structures, key=second))
        self.assertTrue(is_sorted(structures, key=first))


class AddToPointsTestCase(TestCase):

    # the function should sort the points
    def test_sorts_points(self):
        def vk(pt): return pt.value

        pts = [MockPoint(n) for n in range(10, 1, -1)]
        pvs = get_percentiles_for_points(pts)

        self.assertFalse(is_sorted(pts, key=vk))

        assign_percentiles_to_points(pts, pvs)
        self.assertTrue(is_sorted(pts, key=vk))

    # the percentile properties should be set
    def test_adds_percentiles(self):
        pts = [MockPoint(n) for n in range(10, 1, -1)]
        pvs = get_percentiles_for_points(pts)

        none_have_percentile = reduce(lambda sofar, this: sofar and (this.rank is None), pts)
        self.assertTrue(none_have_percentile)

        assign_percentiles_to_points(pts, pvs)

        all_have_percentiles = reduce(lambda sofar, this: sofar and (this.rank is not None), pts)
        self.assertTrue(all_have_percentiles)

    # if we provide percentiles to use, the percentile assigned to every point
    # should be one from the list we specified
    # IMPORTANT
    # This happens to be a nice adversarial test case showing when not all values can
    # be assigned to a percentile bucket! Two values in our range (96 and 100) are *larger*
    # than the value at the 90th percentile (93.6)
    def test_uses_given_percentiles(self):
        ps = [n / 1000 for n in range(1, 1000)]
        ps_check = set(ps)
        
        def checkset(v):
            return v is None or v in ps_check

        pts = [MockPoint(n) for n in range(100, 3, -4)]
        pvs = get_percentiles_for_points(pts)

        assign_percentiles_to_points(pts, pvs)

        all_in_set = reduce(lambda sofar, this: sofar and checkset(this.rank), pts)
        self.assertTrue(all_in_set)

    # after assigning a percentile to a point, the value in that
    # point should be less than the percentile value for that percentile
    # we can check this by independently calculating the percentile values
    # and checking against that
    def values_less_than_their_percentile(self):
        # create points for our values (1-100)
        pts = [MockPoint(v) for v in range(1, 101)]
        pvs = get_percentiles_for_points(pts)

        # turn these into into a dictionary for fast lookups
        percentile_values = {p: pv for (p, pv) in pvs}

        assign_percentiles_to_points(pts)

        # now, for each point, we can lookup the cut off for the percentile it was assigned,
        # and check that this value is larger than the value of the point (i.e. confirm that
        # the point fits inside the bucket it was assigned to)
        for pt in pts:
            with self.subTest(value=pt.value):
                value = pt.value
                rank = pt.rank
                if rank is not None:  # because this can happen...
                    percentile_value = percentile_values[rank]
                    self.assertLessEqual(value, percentile_value)
