from django.conf import settings
from django.conf.urls import include, patterns, url

from .views import DetailView, seed

urlpatterns = [

    url(r'^(?P<pk>\d+)/$', DetailView.as_view(), name='tileset_detail'),
    url(r'^(?P<pk>\d+)/seed$', seed, name='tileset_seed'),
]