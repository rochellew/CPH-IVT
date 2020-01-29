from django.db.models import Value, F
from django.db.models.functions import Concat

from app_api.views.list_all import ListEndpoint
from hda_privileged.models import US_State


class ListAll(ListEndpoint):

    model = US_State

    def get_values_queryset(self, request):
        return US_State.objects.values(
            'fips',
            usps=F('short'),
            name=F('full'),
            search=Concat('short', Value(' '), 'full')
        )
