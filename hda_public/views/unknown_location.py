from django.views.generic import TemplateView

class UnknownLocationView(TemplateView):
    template_name = 'hda_public/unknown_location.html'
