from django.http import JsonResponse
from django.views import View

from django.db.models import F

from hda_privileged.models import US_State, US_County

from app_api.util import search


class Suggestions(View):
    '''
    Given some query, returns a JSON list of objects that might match that query.
    This is used by Bloodhound.js if its local object store does not provide enough
    results for what the user is typing, so the JSON objects use the same format as
    the Bloodhound prefetch data (see also management/commands/generate_prefetch_data.py)

    MUST BE SUBCLASSED
    '''
    limit = 5

    def make_datum(self, object):
        pass

    def stringify_datum(self, result):
        return str(result)

    def filter_model(self, query):
        pass

    # sort results by the difference between the length of the query and
    # the length of the field we were searching in when matching the result
    # (If query is "Mont" and we have results "Monty" and "Montgomery", we want
    # "Monty" to rank higher)
    def rank(self, query, results):
        query_len = len(query)

        def compare(result):
            as_str = self.stringify_datum(result)
            return len(as_str) - query_len

        return sorted(results, key=compare)

    def get(self, request, query=None):
        objects = []

        if query:
            matches = self.filter_model(query)
            datums = [self.make_datum(m) for m in matches.iterator()]
            objects = self.rank(query, datums)[:self.limit]

        return JsonResponse(objects, safe=False)


class StateSuggestions(Suggestions):

    def make_datum(self, obj):
        return search.datum_for_state(obj)

    def filter_model(self, query):
        return US_State.objects.filter(full__icontains=query)


class CountySuggestions(Suggestions):

    def make_datum(self, obj):
        return search.datum_for_county(obj)

    def stringify_datum(self, result):
        return result['value']

    def filter_model(self, query):
        return US_County.objects.filter(search_str__icontains=query)
