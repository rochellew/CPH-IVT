from django.views import View
from django.http import JsonResponse


class ListEndpoint(View):

    model = None

    def get_values_queryset(self, request):
        return self.model.objects.values()

    def get(self, request):
        query = self.get_values_queryset(request)
        items = list(query.iterator())
        return JsonResponse({'values': items})
