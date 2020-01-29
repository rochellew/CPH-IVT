from django.views.generic import TemplateView, ListView

from hda_privileged.models import US_State, US_County, Health_Indicator

class StateView(ListView):
    template_name = 'hda_public/state_list.html'
    paginate_by = '15'
    model = US_State
    context_object_name = "states"

    def get_queryset(self):
        states = US_State.objects.all().order_by('full')
        return states

    def get_context_data(self, **kwargs):
        context = super(StateView, self).get_context_data(**kwargs)
        context['range'] = range(context['paginator'].num_pages)
        return context


class CountyView(ListView):
    template_name = 'hda_public/county_list.html'
    paginate_by = '15'
    model = US_County
    context_object_name = "counties"

    def get_context_data(self, **kwargs):
        context = super(CountyView, self).get_context_data(**kwargs)
        context['range'] = range(context['paginator'].num_pages)
        state_short_name = self.kwargs.get('short', None)

        if state_short_name is not None:
            context['state'] = US_State.objects.filter(short=state_short_name).first().full
            context['state_short_name'] = state_short_name

        return context

    def get_queryset(self):
        state_short_name = self.kwargs.get('short', None)
        counties = None

        if state_short_name is not None:
            associated_state = US_State.objects.filter(short=state_short_name).first()
            counties = associated_state.counties.order_by('name')

        return counties

# have identified a potential problem:
# assume 2 data sets for 1 indicator, one 2017 and one 2018
# let's say the 2017 data set includes county X, but set 2018 does NOT include county X
# when we collect indicators that contain county X, we will find the 2017 data set through
# the 2017 data point for county X, and hence find our indicator object.

# when we go to the chart view, we pass it 3 pieces of information: state, county, and indicator
# the chart view then looks up the latest data set for the given indicator (which will be the 2018 one)
# the data set that is plotted will not include county X, but the URL specifies that we should
# highlight county X.

# hmmm.

class HealthView(TemplateView):
    template_name = 'hda_public/health_indicator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        fips = self.kwargs.get('fips', None)
        state_short = self.kwargs.get('short', None)

        if fips is not None and state_short is not None:
            # get the state the user wants
            state = US_State.objects.get(short=state_short.upper())
            # get the county the user wants
            county = state.counties.get(fips=fips)
            # make a list of every data set containing a data point connected to this county,
            # by starting with the county's data points and going backwards.
            # the 'select_related' does *not* affect the result of the query, only how many database queries are required.
            available_data_sets = [dp.data_set for dp in county.data_points.all().select_related('data_set')]
            # several data sets may be for the same indicator (perhaps different datasets for different years).
            # this extracts the indicator from each dataset into a list, then puts that list into a python set object,
            # which can remove the duplicates for us.
            unique_indicators = set([ds.indicator for ds in available_data_sets])
            # pack up the context - including whole objects so we can use multiple properties in the template
            context['state'] = state
            context['county'] = county
            context['indicators'] = unique_indicators
        else:
            context['error'] = 'Missing a valid state or county identifier in the URL for this page'

        return context

# User chose state path


class HealthStatePathView(TemplateView):
    template_name = 'hda_public/health_indicator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        state_short = self.kwargs.get('short', None)

        # user selected state from dashboard
        if state_short is not None:
            # get the state the user wants
            chosen_state = US_State.objects.get(short=state_short.upper())
            counties = US_County.objects.filter(state=chosen_state)
            for county in counties:
                dp = county.data_points
            # make a list of every data set containing a data point connected to counties in this state,
            # by starting with the county data points and going backwards.
            # the 'select_related' does *not* affect the result of the query, only how many database queries are required.
            available_data_sets = [
                dp.data_set for dp in county.data_points.all().select_related('data_set')]
            # several data sets may be for the same indicator (perhaps different datasets for different years).
            # this extracts the indicator from each dataset into a list, then puts that list into a python set object,
            # which can remove the duplicates for us.
            unique_indicators = set(
                [ds.indicator for ds in available_data_sets])
            # pack up the context - including whole objects so we can use multiple properties in the template
            context['state'] = chosen_state
            context['county'] = counties
            context['indicators'] = unique_indicators
        else:
            context['error'] = 'Missing a valid state or county identifier in the URL for this page'

        return context
