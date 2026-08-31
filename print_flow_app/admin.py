from django.contrib import admin
from .models import Plan, Tenant, Subscription, SubscriptionPayment, User, DarajaConfiguration, Pricing, Document, Printer, PrintJob, Payment, Message

# Register your models here.
admin.site.register(Plan)
admin.site.register(Tenant)
admin.site.register(Subscription)
admin.site.register(SubscriptionPayment)
admin.site.register(User)
admin.site.register(DarajaConfiguration)
admin.site.register(Pricing)
admin.site.register(Document)
admin.site.register(Printer)
admin.site.register(PrintJob)
admin.site.register(Payment)
admin.site.register(Message)
