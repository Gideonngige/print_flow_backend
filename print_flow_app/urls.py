from django.urls import path
from . import views
from .api_views.auth import *
from .api_views.documents import *
from .api_views.payments import *
from .api_views.printing import *

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

    # payments
    path("pay_print_job/", pay_print_job, name="pay_print_job"),
    path("mpesa_callback/", mpesa_callback, name="mpesa_callback"),
    path("print_job_status/<int:print_job_id>/", print_job_status, name="print_job_status"),

    # printing
    path("agent/get_print_job/", get_print_job, name='get_print_job'),
    path("agent/start_printing/", start_printing, name='start_printing'),
    path("agent/complete_print_job/", complete_print_job, name='complete_print_job'),
    path("agent/failed_print_job/", failed_print_job, name='failed_print_job'),
    path("agent/printer_status/",printer_status, name='printer_status'),
    
]