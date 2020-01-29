from django.db.models import Value, F
from django.db.models.functions import Concat

from app_api.views.list_all import ListEndpoint
from hda_privileged.models import US_County


class ListAll(ListEndpoint):

    model = US_County

    def get_values_queryset(self, request):
        return US_County.objects.values(
            'name', 'fips5', 'state',
            search=Concat('name', Value(' '), 'state__short')
        )
