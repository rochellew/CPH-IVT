from django.views.generic import TemplateView

class HomeView(TemplateView):
    '''
    Displays the home page. Since the home page is static, this is easy.
    '''
    template_name = 'hda_public/dashboard.html'