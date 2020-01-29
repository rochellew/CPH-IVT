from django.urls import path

import app_api.views.county as county
import app_api.views.state as state

from app_api.views.search import StateSuggestions, CountySuggestions
from app_api.views.chart import PercentileSeries, PointSeries


app_name = 'api'
urlpatterns = [
    # entities
    path('county/list/', county.ListAll.as_view()),
    path('state/list/', state.ListAll.as_view()),
    # search suggestions
    path('search/suggestions/state/<str:query>', StateSuggestions.as_view(), name='suggest_state'),
    path('search/suggestions/county/<str:query>', CountySuggestions.as_view(), name='suggest_county'),
    # async chart series
    path('chart/percentiles/<int:data_set_id>/', PercentileSeries.as_view(), name='chart_percentiles'),
    path('chart/points/<int:data_set_id>', PointSeries.as_view(), name='chart_points'),
]