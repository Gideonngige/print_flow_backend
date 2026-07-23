from django.urls import path
from . import views
from .api_views.auth import *
from .api_views import *

urlpatterns = [
    path('', views.index, name='index'),

    # auth
    path('send_test_email/', send_test_email, name='send_test_email'),
    path('signup/', signup, name='signup'),
    path('verify_email/', verify_email, name='verify_email'),
    path('signin/', signin, name='signin'),
    path('request_reset/', request_reset, name='request_reset'),
    path('reset_password/', reset_password, name='reset_password'),
    path('refresh_token', refresh_token, name='refresh_token'),
    path('delete_account/', delete_account, name='delete_account'),
    path('auth_check/', auth_check, name='auth_check'),

    # documents
    path("upload_document/", upload_document, name="upload_document"),
    path("create_print_job/", create_print_job, name="create_print_job"),
    
    
]