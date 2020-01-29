from django.core.management import BaseCommand, CommandError
from hda_privileged.models import *
from hda_privileged.percentile import get_percentiles_for_points, assign_percentiles_to_points

import argparse
import random
import math

from itertools import dropwhile

def _create_data_set(indicator, year):
    # don't overwrite an existing data set!
    if indicator.data_sets.filter(year=year).exists():
        raise CommandError(f'Indicator {indicator.name} already has a data set for year {year}, aborting')
    else:
        # https://docs.djangoproject.com/en/2.1/topics/db/queries/#additional-methods-to-handle-related-objects
        return indicator.data_sets.create(year=year)

def _create_data_points(data_set, max_points, mean, stddev):
    make_point = lambda c: Data_Point(value=random.gauss(mean, stddev), county=c, data_set=data_set)
    counties = US_County.objects.all()[:max_points]
    return [make_point(c) for c in counties.iterator()]

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-i', '--indicator', default='Test Indicator')
        parser.add_argument('-y', '--year', type=int, default=2018)
        parser.add_argument('-c', '--count', type=int, default=None)
        parser.add_argument('-m', '--mean', type=float, default=0.5)
        parser.add_argument('-s', '--sigma', type=float, default=None)

    def handle(self, *args, **options):
        indicator_name = options['indicator']
        year = options['year']
        max_points = options['count'] if options['count'] else US_County.objects.count()
        mean = options['mean']
        stddev = options['sigma'] if options['sigma'] else mean / 5

        self.stdout.write(f"Creating random data for {indicator_name}, {year}")

        # https://docs.djangoproject.com/en/2.1/ref/models/querysets/#get-or-create
        indicator, _ = Health_Indicator.objects.get_or_create(name=indicator_name)
        data_set = _create_data_set(indicator, year)

        self.stdout.write(f"Using indicator w/ id {indicator.id}, data set w/ id {data_set.id}")

        random.seed()

        points = _create_data_points(data_set, max_points, mean, stddev)
        self.stdout.write(f"Created {len(points)} new data points")

        self.stdout.write("Adding percentiles...")
        percentile_values = get_percentiles_for_points(points)
        assign_percentiles_to_points(points, percentile_values)

        pv_models = [Percentile(rank=p, value=pv, data_set=data_set) for (p, pv) in percentile_values]

        # https://docs.djangoproject.com/en/2.1/ref/models/querysets/#bulk-create
        # it mentions several caveats, but it seems sufficient for this use case
        self.stdout.write("Saving data points")
        Data_Point.objects.bulk_create(points)
        Percentile.objects.bulk_create(pv_models)

