import json

from app_api.views.get_json import GetJSON
from hda_privileged.models import Data_Set, US_County, US_State


class PercentileSeries(GetJSON):

    def get_data(self, data_set_id):
        # THROWS
        data_set = Data_Set.objects.get(pk=data_set_id)
        percentiles = data_set.percentiles.all().order_by('rank')
        spline_points = [(round(p.rank * 100, 2), p.value) for p in percentiles]
        config = {
            'name': 'Percentiles',
            'type': 'spline',
            'color': 'gray',
            'enableMouseTracking': False,
            'marker': {
                'enabled': False,
            },
            'zIndex': -1,
            'data': spline_points,
        }
        return {'config': config}

class PointSeries(GetJSON):

    def try_get_county(self, fips_code):
        try:
            return US_County.objects.get(fips5=fips_code)
        except US_County.DoesNotExist:
            return None

    def try_get_point(self, data_set, county):
        return data_set.data_points.filter(county=county).first()

    def get_requested_counties(self):
        requested_state = self.request.GET.get('state', None)
        if requested_state:
            state = US_State.objects.get(pk=requested_state.upper())  # THROWS
            return ([county for county in state.counties.all().iterator()], [])
        else:
            requested_fips = self.request.GET.get('county', None)

            if requested_fips is None:
                raise Exception('Endpoint must be called with a state or county query string')

            fips_list = requested_fips.split(',')
            query_results = [(fips, self.try_get_county(fips)) for fips in fips_list]
            matched = [county for (_, county) in query_results if county]
            unmatched = [fips for (fips, county) in query_results if not county]
            return (matched, unmatched)


    def get_requested_points(self, data_set, counties):
        query_results = [(county, self.try_get_point(data_set, county)) for county in counties]
        points = [point for (_, point) in query_results if point]
        unmatched = [county for (county, point) in query_results if not point]
        return (points, unmatched)

    def point_to_dict(self, point):
        return {
            'x': round(point.rank * 100, 2),
            'y': point.value,
            'name': point.county.name,
        }

    def get_data(self, data_set_id):

        data_set = Data_Set.objects.get(pk=data_set_id)  # THROWS

        (counties, unmatched_fips) = self.get_requested_counties()  # THROWS

        (points, unmatched_counties) = self.get_requested_points(data_set, counties)

        config = {
            'name': 'Values',
            'type': 'scatter',
            'color': 'darkred',
            'enableMouseTracking': True,
            'marker': {
                'radius': 3,
                'symbol': 'circle',
            },
            'tooltip': {
                'pointFormat': r'{point.name}<br/>p: <b>{point.x}%</b><br/>v: <b>{point.y}</b><br/>',
                'valueDecimals': 1,
            },
            'data': [self.point_to_dict(p) for p in points]
        }

        errors = dict()

        if len(unmatched_fips) > 0:
            errors['no_county'] = '; '.join(unmatched_fips)

        if len(unmatched_counties) > 0:
            errors['no_fips'] = '; '.join(
                [f"{county.name}, {county.state.short}" for county in unmatched_counties]
            )

        return {
            'config': config,
            'errors': errors,
        }



