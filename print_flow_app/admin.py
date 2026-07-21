from django.contrib import admin
from .models import User, Document, PrintJob, Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Document)
admin.site.register(PrintJob)
admin.site.register(Payment)
