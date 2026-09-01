from django.urls import path
from . import views
from .api_views.auth import *
from .api_views.documents import *
from .api_views.payments import *
from .api_views.printing import *
from .api_views.dashboard import *
from .api_views.admin import *
from .api_views.messages import *

# new 
from .api_views.business import *
from .api_views.customers import *
from .api_views.print_jobs import *
from .api_views.pricing import *
from .api_views.business_documents import *
from .api_views.printers import *
from .api_views.business_payments import *
from .api_views.subscription import *
from .api_views.staff import *
from .api_views.settings import *
from .api_views.business_messages import *

urlpatterns = [
    path('', views.index, name='index'),

    # auth
    path('auth/send_test_email/', send_test_email, name='send_test_email'),
    path('auth/signup/', register_business, name='signup'),
    path('auth/verify_email/', verify_email, name='verify_email'),
    path('auth/signin/', signin, name='signin'),
    path('auth/request_reset/', request_reset, name='request_reset'),
    path('auth/reset_password/', reset_password, name='reset_password'),
    path('auth/refresh_token/', refresh_token, name='refresh_token'),
    path('auth/delete_account/', delete_account, name='delete_account'),
    path('auth/auth_check/', auth_check, name='auth_check'),


    # business
    path("business/dashboard/", business_dashboard, name="business_dashboard"),


    # customers
    path("business/customers/", business_customers, name="business_customers"),
    path("business/customers/<int:customer_id>/", business_customer_detail, name="business_customer_detail"),
    path("business/customers/<int:customer_id>/status/", update_customer_status, name="update_customer_status"),


    # print jobs
    path("business/print-jobs/", business_print_jobs, name="business_print_jobs"),
    path("business/print-jobs/<int:job_id>/", business_print_job_detail, name="business_print_job_detail"),
    path("business/print-jobs/<int:job_id>/status/", update_business_print_job_status, name="update_business_print_job_status"),
    path("business/print-jobs/<int:job_id>/printer/", assign_print_job_printer, name="assign_print_job_printer"),


    # pricing
    path("business/pricing/", business_pricing, name="business_pricing"),
    path("business/pricing/<int:pricing_id>/", update_business_pricing, name="update_business_pricing"),
    path("business/pricing/<int:pricing_id>/delete/", delete_business_pricing, name="delete_business_pricing"),

    # business documents
    path("business/documents/", business_documents, name="business_documents"),
    path("business/documents/<int:document_id>/", business_document_detail, name="business_document_detail"),
    path("business/documents/<int:document_id>/delete/", delete_business_document, name="delete_business_document"),

    # printers
    path("business/printers/", business_printers, name="business_printers"),
    path("business/printers/<int:printer_id>/", business_printer_detail, name="business_printer_detail"),
    path("business/printers/<int:printer_id>/update/",update_business_printer, name="update_business_printer"),
    path("business/printers/<int:printer_id>/default/", set_default_printer, name="set_default_printer"),
    path("business/printers/<int:printer_id>/delete/", delete_business_printer, name="delete_business_printer"),


    # business payments
    path("business/payments/", business_payments, name="business_payments"),
    path("business/payments/<int:payment_id>/", business_payment_detail, name="business_payment_detail"),

    # subscription
    path("business/subscription/", business_subscription, name="business_subscription"),
    path("business/subscription/change-plan/", change_business_plan, name="change_business_plan"),
    path("business/subscription/auto-renew/", update_subscription_auto_renew, name="update_subscription_auto_renew"),

    # staff
    path("business/staff/", business_staff, name="business_staff"),
    path("business/staff/<int:staff_id>/", business_staff_detail, name="business_staff_detail"),
    path("business/staff/<int:staff_id>/update/", update_business_staff, name="update_business_staff"),
    path("business/staff/<int:staff_id>/status/", update_staff_status, name="update_staff_status"),
    path("business/staff/<int:staff_id>/password/", reset_staff_password, name="reset_staff_password"),
    path("business/staff/<int:staff_id>/delete/", delete_business_staff, name="delete_business_staff"),

    # settings
    path("business/settings/", business_settings, name="business_settings"),
    path("business/settings/daraja/", business_daraja_settings, name="business_daraja_settings"),

    # business messages
    path("business/messages/", business_messages, name="business_messages"),
    path("business/messages/<int:message_id>/", business_message_detail, name="business_message_detail"),
    path("business/messages/<int:message_id>/update/", update_business_message, name="update_business_message"),
    path("business/messages/<int:message_id>/delete/", delete_business_message, name="delete_business_message"),

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