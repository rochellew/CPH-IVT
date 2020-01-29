import argparse
import json

from pathlib import Path

from django.core.management import BaseCommand, CommandError

from app_api.util import search
from hda_privileged.models import US_County, US_State

def pathtype(value):
    path = Path(value)
    if not path.parent.exists():
        raise argparse.ArgumentTypeError(f"Folder")

def county_data():
    query = US_County.objects.all().order_by('state', 'name')
    data = [search.datum_for_county(obj) for obj in query.iterator()]
    return data

def state_data():
    query = US_State.objects.all().order_by('full')
    data = [search.datum_for_state(obj) for obj in query.iterator()]
    return data

def indent_level(is_pretty):
    return 2 if is_pretty else None

def separators(is_pretty):
    return (',', ': ') if is_pretty else (',', ':')

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'type',
            choices=['county', 'state'],
            help='Choose between generating prefetch data for counties or states'
        )
        parser.add_argument(
            '-o', '--output-path',
            type=pathtype,
            default=Path.cwd() / 'prefetch.json',
            help='File path to save prefetch data to'
        )
        parser.add_argument(
            '-p', '--pretty',
            action='store_true',
            help='Formats JSON for readability instead of compactness'
        )



    def handle(self, *args, **options):
        output_path = options['output_path']
        is_pretty = options.get('pretty', False)

        type_map = {
            'state': state_data,
            'county': county_data
        }

        data = type_map[options['type']]()

        with output_path.open(mode='w') as fp:
            json.dump(
                data,
                fp,
                indent=indent_level(is_pretty),
                separators=separators(is_pretty),
                sort_keys=is_pretty
            )
