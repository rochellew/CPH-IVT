# Views that handle displaying multiple small charts for a state or county,
# along with a list of indicators that have data points for that location.
#
# The page is designed so that users can see an overview of their location's place
# for the most important health indicators, without having to choose one.
#
# IndicatorOverviewBase is a base class that has State and County subclasses,
# since the logic for those is slightly different.
#
# ~ Matthew Seiler

from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.db.models import Count

from hda_privileged.models import US_State, US_County, Health_Indicator, Data_Set, Data_Point

from util.collections import index_selector, group_by_selector


class IndicatorOverviewBase(View):
    """
    Base class for overview page views; provides a framework for the state and county views
    to fill in. The key differences are the query string used to request chart data on the page
    (get_chart_location_parameter), the format of the name of the place being displayed,
    (get_place_name), and which data sets are involved (get_related_data_sets).

    Note that this subclasses View, not TemplateView!
    """

    def handle_missing_parameter(self):
        return redirect('unknown_location')

    def get_chart_location_parameter(self):
        """
        Get the query string paramater to use when building URLs that request a chart or chart
        data for the requested location (e.g. "state=VA" or "county=12345")
        :return: the query string parameter with chart URLs in the template
        :rtype: str
        """
        pass

    def get_place_name(self):
        """
        Return a string to use for the name of the requested location.
        Subclasses MUST implement this!
        :return: a display-able name for the requested county or state
        :rtype: str
        """
        pass

    def get_related_data_sets(self):
        """
        Return every data set containing a data point for the requested location.
        Subclasses MUST implement this!
        :return: query set of data sets related to the requested location
        :rtype: QuerySet<Data_Set>
        """
        pass

    def get(self, request, *args, **kwargs):
        # every data set related to the requested location
        data_set_meta = self.get_related_data_sets().values('id', 'year', 'indicator')
        # group these data sets by indicator
        grouped_by_indicator = group_by_selector(
            data_set_meta.iterator(),
            index_selector('indicator')
        )
        # sort each group by year, descending
        for (_, dsm) in grouped_by_indicator.items():
            dsm.sort(key=index_selector('year'), reverse=True)
        # now change the map so each indicator ID points to only the ID of the most recent data set:
        data_set_for_indicator = {ind: dsm[0]['id'] for (ind, dsm) in grouped_by_indicator.items()}

        # at this point, we know what data sets and indicators are available, but we don't
        # actually have the full indicator objects queried from the database.

        # What has to go on this page?
        # 1. One chart for each important indicator
        #    a. indicator name
        #    b. data set ID
        #    c. county/counties to plot
        # 2. One link for each indicator
        #    a. indicator name (for display)
        #    b. data set ID (for URL)
        #    c. county or counties (for URL)

        # So it's the same for each. Let's get all our indicator objects:
        indicator_ids = set(data_set_for_indicator.keys())
        indicators = Health_Indicator.objects.filter(id__in=indicator_ids)

        # whew. now let's build a list of dictionaries to use in context.
        # here's a little mapping function:
        def make_indicator_ctx(indicator):
            return {
                'name': indicator.name,
                'data_set_id': data_set_for_indicator[indicator.id]
            }

        # now use the mapping function to construct lists of dictionaries for the template context:
        all_indicator_context = []
        important_indicator_context = []
        for indicator in indicators:
            ctx = make_indicator_ctx(indicator)
            all_indicator_context.append(ctx)
            if indicator.important:
                important_indicator_context.append(ctx)

        context = dict()

        context['all_indicators'] = all_indicator_context
        context['important_indicators'] = important_indicator_context
        context['place_name'] = self.get_place_name()
        context['place_query_string'] = self.get_chart_location_parameter()

        return render(request, 'hda_public/overview.html', context=context)


class IndicatorOverviewCounty(IndicatorOverviewBase):
    """
    The IndicatorOverview View for displaying a specific county
    """

    def get_chart_location_parameter(self):
        return f"county={self.county.fips5}"

    def get_place_name(self):
        county_name = self.county.name
        state_name = self.state.short
        return f"{county_name}, {state_name}"

    def get_related_data_sets(self):
        # get all the data points this county is in:
        dps = self.county.data_points.all()
        # then get all the data sets that have one of those data points:
        return Data_Set.objects.filter(data_points__in=dps)

    def get(self, request, state=None, county=None):
        if state is None or county is None:
            return self.handle_missing_parameter()

        try:
            self.state = US_State.objects.get(pk=state.upper())
        except US_State.DoesNotExist:
            return self.handle_missing_parameter()

        try:
            self.county = self.state.counties.get(fips=county)
        except US_County.DoesNotExist:
            return self.handle_missing_parameter()

        return super(IndicatorOverviewCounty, self).get(request)


class IndicatorOverviewState(IndicatorOverviewBase):
    """
    The IndicatorOverview View for displaying a particular state
    """

    def get_chart_location_parameter(self):
        return f"state={self.state.short}"

    def get_place_name(self):
        return f"{self.state.full}"

    def get_related_data_sets(self):
        # get all the counties in the state:
        counties = self.state.counties.all()
        # get all the data points that point at one of the counties:
        dps = Data_Point.objects.filter(county__in=counties)
        # then get all the data sets that have one of those data points:
        return Data_Set.objects.filter(data_points__in=dps)

    def get(self, request, state=None):
        if state is None:
            return self.handle_missing_parameter()

        try:
            self.state = US_State.objects.get(pk=state.upper())
        except US_State.DoesNotExist:
            return self.handle_missing_parameter()

        return super(IndicatorOverviewState, self).get(request)
