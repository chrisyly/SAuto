from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    url(r'^$', views.index, name = 'index'),
    url(r'^vendor_config/$', views.vendorConfig, name = 'vendor configuration'),
    url(r'^rf_matrix_config/$', views.rfMatrixConfig, name = 'rf matrix configuration'),
    url(r'^jfw_config/$', views.jfwConfig, name = 'jfw configuration'),
    url(r'^mxa_config/$', views.mxaConfig, name = 'mxa configuration'),
    url(r'^jenkins_config/$', views.jenkinsConfig, name = 'jenkins configuration'),
	url(r'^database_config/$', csrf_exempt(views.updateDatabase), name = 'database configuration'),
    ## url(r'^api/test/$', views.testAPI, name = 'rest api'),
]
