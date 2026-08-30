from django.contrib import admin
from .models import Plan, Tenant, Subscription, SubscriptionPayment, User, Document, PrintJob, Payment, Message

# Register your models here.
admin.site.register(Plan)
admin.site.register(Tenant)
admin.site.register(Subscription)
admin.site.register(SubscriptionPayment)
admin.site.register(User)
admin.site.register(Document)
admin.site.register(PrintJob)
admin.site.register(Payment)
admin.site.register(Message)
