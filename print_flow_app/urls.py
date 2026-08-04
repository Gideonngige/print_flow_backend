from django.urls import path
from . import views
from .api_views.auth import *
from .api_views.documents import *
from .api_views.payments import *
from .api_views.printing import *
from .api_views.dashboard import *
from .api_views.admin import *
from .api_views.messages import *

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
    path("my_documents/", my_documents, name="my_documents"),
    path("documents/<int:document_id>/delete/", delete_document, name="delete_document"),

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
    path("print_history/", print_history, name="print_history"),
    path("print_jobs/<int:print_job_id>/receipt/", download_print_receipt, name="download_print_receipt"),

    # dashboard
    path("user_dashboard/", user_dashboard, name='user_dashboard'),


    # admin
    # Admin APIs
    path("admin_dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin_users/", admin_users, name="admin_users"),
    path("admin_users/<int:user_id>/status/", update_user_status, name="update_user_status"),
    path("admin_print_jobs/", admin_print_jobs, name="admin_print_jobs"),
    path("admin_print_jobs/<int:print_job_id>/status/", admin_update_print_job, name="admin_update_print_job"),
    path("admin_print_jobs/<int:print_job_id>/retry/", retry_print_job, name="retry_print_job"),
    path("admin_payments/", admin_payments, name="admin_payments"),
    path("admin_documents/", admin_documents,name="admin_documents"),

    # Contact messages
    path("send_message/", send_message, name="send_message"),
    path("admin_messages/", admin_messages, name="admin_messages"),
    path("admin_messages/<int:message_id>/status/", update_message_status, name="update_message_status"),
    path("admin_messages/<int:message_id>/delete/", delete_message, name="delete_message"),

    
]