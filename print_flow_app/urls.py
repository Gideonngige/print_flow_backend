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
from .api_views.customer_dashboard import *
from .api_views.tenant import *
from .api_views.customer_profile import *
from .api_views.platform import *
from .api_views.platform_tenants import *
from .api_views.platform_plans import *
from .api_views.platform_subscription import *
from .api_views.platform_payments import *
from .api_views.platform_users import *
from .api_views.print_agent_apis import *

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
    path('auth/customer-signup/', customer_signup, name='customer_signup'),
    path("auth/customer-signin/", customer_signin, name="customer_signin"),


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
    path("business/print-agents/", business_print_agents, name="business_print_agents"),
    path("business/print-agents/<int:agent_id>/", business_print_agent_detail, name="business_print_agent_detail"),
    path("business/print-agents/<int:agent_id>/regenerate-key/", business_regenerate_agent_key, name="business_regenerate_agent_key"),
    path("business/print-agents/<int:agent_id>/disconnect-printer/", business_disconnect_agent_printer, name="business_disconnect_agent_printer"),
    path("business/print-jobs/recover-stale/", recover_stale_jobs, name="recover_stale_jobs"),


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

    # customer dashboard
    path("customer/dashboard/",customer_dashboard, name="customer_dashboard"),


    # tenant
    path("public/business/<slug:slug>/", public_tenant_detail, name="public_tenant_detail"),



    # documents
    path("customer/upload-document/", upload_document, name="upload_document"),
    path("customer/create-print-job/", create_print_job, name="create_print_job"),
    path("customer/documents/", my_documents, name="my_documents"),
    path("customer/documents/<int:document_id>/delete/", delete_document, name="delete_document"),

    # payments
    path("customer/pay-print-job/", pay_print_job, name="pay_print_job"),
    path("customer/mpesa-callback/", mpesa_callback, name="mpesa_callback"),
    path("customer/print-job-status/<int:print_job_id>/", print_job_status, name="print_job_status"),

    # printing
    path("agent/get_print_job/", get_print_job, name='get_print_job'),
    path("agent/start_printing/", start_printing, name='start_printing'),
    path("agent/complete_print_job/", complete_print_job, name='complete_print_job'),
    path("agent/failed_print_job/", failed_print_job, name='failed_print_job'),
    path("agent/printer_status/",printer_status, name='printer_status'),
    path("customer/print-history/", print_history, name="print_history"),
    path("customer/print-jobs/<int:print_job_id>/receipt/", download_print_receipt, name="download_print_receipt"),

    # customer profile
    path("customer/profile/", customer_profile, name="customer_profile"),

    # platform 
    path("platform/dashboard/", platform_dashboard, name="platform_dashboard"),

    # platform tenants
    path("platform/tenants/", platform_tenants, name="platform_tenants"),
    path("platform/tenants/<int:tenant_id>/status/", platform_update_tenant_status, name="platform_update_tenant_status"),
    path("platform/tenants/<int:tenant_id>/", platform_tenant_detail, name="platform_tenant_detail"),
    path("platform/tenants/<int:tenant_id>/update/", platform_update_tenant, name="platform_update_tenant"),

    # platform plans
    path("platform/plans/", platform_plans, name="platform_plans"),
    path("platform/plans/<int:plan_id>/", platform_plan_detail, name="platform_plan_detail"),

    # platform subscription
    path("platform/subscriptions/", platform_subscriptions, name="platform_subscriptions"),
    path("platform/subscriptions/<int:subscription_id>/", platform_update_subscription, name="platform_update_subscription"),
    path("platform/subscriptions/<int:subscription_id>/extend/", platform_extend_subscription, name="platform_extend_subscription"),

    # platform payments
    path("platform/payments/", platform_subscription_payments, name="platform_subscription_payments"),
    path("platform/payments/<int:payment_id>/", platform_subscription_payment_detail, name="platform_subscription_payment_detail"),
    path("platform/payments/<int:payment_id>/update/", platform_update_subscription_payment, name="platform_update_subscription_payment"),

    # platform users
    path("platform/users/", platform_users, name="platform_users"),
    path("platform/users/<int:user_id>/", platform_user_detail, name="platform_user_detail"),
    path("platform/users/<int:user_id>/status/", platform_update_user_status, name="platform_update_user_status"),

    # print agent APIs
    path("agent/config/", agent_config, name="agent_config"),
    path("agent/heartbeat/", agent_heartbeat, name="agent_heartbeat"),
    path("agent/next-job/", agent_next_job, name="agent_next_job"),
    path("agent/start-printing/",agent_start_printing, name="agent_start_printing"),
    path("agent/complete-job/", agent_complete_job, name="agent_complete_job"),
    path("agent/fail-job/", agent_fail_job, name="agent_fail_job"),
    path("agent/printers/sync/", agent_sync_printers, name="agent_sync_printers"),
    path("business/discovered-printers/", business_discovered_printers, name="business_discovered_printers"),
    path("business/printers/<int:printer_id>/map-local/", business_map_local_printer, name="business_map_local_printer"),







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