from django.http import JsonResponse, HttpResponseServerError
from django.views import View


class GetJSON(View):

    def get_data(self, *args, **kwargs):
        return dict()

    # def get(self, request, *args, **kwargs):
    #     data = self.get_data(*args, **kwargs)
    #     return JsonResponse(data)

    def get(self, request, *args, **kwargs):
        try:
            data = self.get_data(*args, **kwargs)
            return JsonResponse(data)
        except Exception as exc:
            return HttpResponseServerError(str(exc))
