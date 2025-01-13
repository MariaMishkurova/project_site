from django.conf import settings

def global_settings(request):
    return {
        'currrent_login': settings.MY_GLOBAL_VARIABLE
    }