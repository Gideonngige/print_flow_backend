from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

# -----------------------------
# 1. User Model
# -----------------------------
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True) 
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expo_token = models.CharField(max_length=100, default="")
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username' 
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"


class Document(models.Model):
    CHOICES = [
        ('uploaded', 'Uploaded'),
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('printed', 'Printed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/")
    original_name = models.CharField(max_length=255)
    cloudinary_public_id = models.CharField(max_length=255, blank=True)
    cloudinary_url = models.URLField(blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.IntegerField()
    pages = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=CHOICES, default="uploaded")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.original_name



class PrintJob(models.Model):
    CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('queued', 'Queued'),
        ('printing', 'Printing'),
        ('printed', 'Printed'),
        ('failed', "Failed"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    copies = models.IntegerField(default=1)
    paper_size = models.CharField(max_length=100, blank=True)
    double_sided = models.BooleanField(default=False)
    color = models.BooleanField(default=False)
    double_sided = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Print Job #{self.id} - {self.user.username}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('m-pesa', 'M-pesa'),
        ('paystack', 'Paystack'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    print_job = models.OneToOneField(PrintJob, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    color_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paper_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=100,blank=True,null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Job #{self.print_job.id}"

