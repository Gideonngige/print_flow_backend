from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal


# ============================================================
# 7. SAAS PLAN / PACKAGE
# ============================================================

class Plan(models.Model):

    BILLING_CYCLES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    # Price for the selected billing cycle
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLES,
        default="monthly"
    )

    # ========================================================
    # Usage limits
    # ========================================================

    max_users = models.PositiveIntegerField(
        default=1
    )

    max_documents = models.PositiveIntegerField(
        default=100
    )

    max_print_jobs = models.PositiveIntegerField(
        default=100
    )

    max_storage_mb = models.PositiveIntegerField(
        default=500
    )

    # ========================================================
    # Features
    # ========================================================

    allow_color_printing = models.BooleanField(
        default=True
    )

    allow_double_sided = models.BooleanField(
        default=True
    )

    allow_multiple_printers = models.BooleanField(
        default=False
    )

    allow_staff_accounts = models.BooleanField(
        default=False
    )

    allow_custom_domain = models.BooleanField(
        default=False
    )

    advanced_reports = models.BooleanField(
        default=False
    )

    api_access = models.BooleanField(
        default=False
    )

    priority_support = models.BooleanField(
        default=False
    )

    # ========================================================
    # Plan status
    # ========================================================

    is_active = models.BooleanField(
        default=True
    )

    is_popular = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


# ============================================================
# 1. TENANT / BUSINESS
# ============================================================

class Tenant(models.Model):

    name = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=100,
        unique=True
    )

    # Used for:
    # joetech.printflow.co.ke
    subdomain = models.CharField(
        max_length=100,
        unique=True
    )

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    logo = models.URLField(
        blank=True,
        null=True
    )

    # Useful for future custom domains
    custom_domain = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        if not self.subdomain:
            self.subdomain = self.slug

        super().save(*args, **kwargs)

    @property
    def portal_url(self):
        return f"https://{self.subdomain}.printflow.co.ke"

    def __str__(self):
        return self.name



# ============================================================
# 8. SUBSCRIPTION
# ============================================================

class Subscription(models.Model):

    STATUS_CHOICES = [
        ("trial", "Trial"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
    ]

    tenant = models.OneToOneField(
        "Tenant",
        on_delete=models.CASCADE,
        related_name="subscription"
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="trial"
    )

    # ========================================================
    # Subscription dates
    # ========================================================

    start_date = models.DateTimeField(
        default=timezone.now
    )

    current_period_start = models.DateTimeField(
        default=timezone.now
    )

    current_period_end = models.DateTimeField()

    trial_start = models.DateTimeField(
        null=True,
        blank=True
    )

    trial_end = models.DateTimeField(
        null=True,
        blank=True
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # ========================================================
    # Auto renewal
    # ========================================================

    auto_renew = models.BooleanField(
        default=True
    )

    # ========================================================
    # Payment provider information
    # ========================================================

    payment_method = models.CharField(
        max_length=30,
        blank=True
    )

    provider_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    provider_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.tenant.name} - "
            f"{self.plan.name}"
        )


# ============================================================
# 9. SUBSCRIPTION PAYMENT
# ============================================================

class SubscriptionPayment(models.Model):

    PAYMENT_METHODS = [
        ("m-pesa", "M-Pesa"),
        ("paystack", "Paystack"),
        ("card", "Card"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    tenant = models.ForeignKey(
        "Tenant",
        on_delete=models.CASCADE,
        related_name="subscription_payments"
    )

    # ========================================================
    # Amount
    # ========================================================

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default="KES"
    )

    # ========================================================
    # Payment method
    # ========================================================

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # ========================================================
    # Transaction information
    # ========================================================

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    checkout_request_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    merchant_request_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ========================================================
    # Payment status
    # ========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # ========================================================
    # Billing period this payment covers
    # ========================================================

    period_start = models.DateTimeField(
        null=True,
        blank=True
    )

    period_end = models.DateTimeField(
        null=True,
        blank=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.tenant.name} - "
            f"KES {self.amount} - "
            f"{self.status}"
        )


# ============================================================
# 2. USER
# ============================================================

class UserManager(BaseUserManager):

    def create_user(
        self,
        username,
        email,
        password=None,
        **extra_fields
    ):

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

    def create_superuser(
        self,
        username,
        email,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault(
            "is_staff",
            True
        )

        extra_fields.setdefault(
            "is_superuser",
            True
        )

        extra_fields.setdefault(
            "is_active",
            True
        )

        extra_fields.setdefault(
            "role",
            "platform_admin"
        )

        return self.create_user(
            username,
            email,
            password,
            **extra_fields
        )


class User(AbstractUser):

    ROLE_CHOICES = [

        # PrintFlow owner/platform administrator
        (
            "platform_admin",
            "Platform Admin"
        ),

        # Business owner
        (
            "business_admin",
            "Business Admin"
        ),

        # Business employee
        (
            "staff",
            "Staff"
        ),

        # Customer using the printing service
        (
            "customer",
            "Customer"
        ),
    ]

    # Every user except platform admins belongs to
    # a particular business.
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True
    )

    email = models.EmailField(
        unique=True
    )

    username = models.CharField(
        max_length=150,
        unique=True
    )

    full_name = models.CharField(
        max_length=100
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="customer"
    )

    phone_verified = models.BooleanField(
        default=False
    )

    email_verified = models.BooleanField(
        default=False
    )

    email_verification_token = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    reset_token = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    expo_token = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    date_joined = models.DateTimeField(
        default=timezone.now
    )

    is_active = models.BooleanField(
        default=True
    )

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):

        return (
            f"{self.username} "
            f"({self.role})"
        )


# ============================================================
# 3. DOCUMENT
# ============================================================

class Document(models.Model):

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("pending", "Pending"),
        ("printing", "Printing"),
        ("printed", "Printed"),
        ("failed", "Failed"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    # Cloudinary URL
    cloudinary_url = models.URLField(
        blank=True
    )

    cloudinary_public_id = models.CharField(
        max_length=500,
        blank=True
    )

    original_name = models.CharField(
        max_length=500
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True
    )

    size = models.BigIntegerField()

    pages = models.IntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.original_name


# ============================================================
# 4. PRINT JOB
# ============================================================

class PrintJob(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("queued", "Queued"),
        ("printing", "Printing"),
        ("printed", "Printed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="print_jobs"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="print_jobs"
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="print_jobs"
    )

    copies = models.PositiveIntegerField(
        default=1
    )

    paper_size = models.CharField(
        max_length=50,
        default="A4"
    )

    double_sided = models.BooleanField(
        default=False
    )

    color = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"Print Job #{self.id} - "
            f"{self.user.username}"
        )


# ============================================================
# 5. PAYMENT
# ============================================================

class Payment(models.Model):

    PAYMENT_METHODS = [
        ("m-pesa", "M-Pesa"),
        ("paystack", "Paystack"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    print_job = models.OneToOneField(
        PrintJob,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    color_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    paper_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    mpesa_receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    checkout_request_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"Payment #{self.id} "
            f"- Job #{self.print_job.id}"
        )


# ============================================================
# 6. MESSAGE
# ============================================================

class Message(models.Model):

    STATUS_CHOICES = [
        ("unread", "Unread"),
        ("read", "Read"),
        ("replied", "Replied"),
        ("closed", "Closed"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    # Optional because visitors can contact
    # a business without having an account.
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages"
    )

    name = models.CharField(
        max_length=150
    )

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    subject = models.CharField(
        max_length=255,
        blank=True,
        default="General Enquiry"
    )

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unread"
    )

    admin_notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    replied_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):

        return (
            f"{self.name} - "
            f"{self.subject}"
        )