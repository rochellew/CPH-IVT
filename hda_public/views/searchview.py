
from django.views.generic import TemplateView

from hda_privileged.models import US_County, US_State

class SearchView(TemplateView):
    template_name = 'hda_public/search_results.html'

    def find_county_results(self, query):
        # Orders results first by state, then by name. This does not put the most relevant result
        # first, but groups results from the same state together, which may make them easier to scan through?
        matches = US_County.objects.filter(search_str__icontains=query).order_by('state', 'name')
        # truncate to no more than 100 results!
        return list(matches.iterator())[:100]

    def find_state_results(self, query):
        name_matches = US_State.objects.filter(full__istartswith=query)
        abbrv_matches = US_State.objects.filter(short__istartswith=query)
        name_set = set(name_matches.iterator())
        abbrv_set = set(abbrv_matches.iterator())
        all_set = name_set | abbrv_set  # set union
        return sorted(all_set, key=lambda s: s.full)

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)

        query_str = self.request.GET.get('query', '')

        if len(query_str) < 1:
            context['error'] = 'Please provide some text to search with'
            return context

        context['query'] = query_str

        context['counties'] = self.find_county_results(query_str)
        context['states'] = self.find_state_results(query_str)

        return context
