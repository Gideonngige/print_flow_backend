from .common_imports import *
from print_flow_app.services.mpesa import (
    initiate_stk_push,
    normalize_mpesa_phone,
)
from print_flow_app.utils.subscription import (
    get_subscription_state,
)


# ============================================================
# BUSINESS SUBSCRIPTION OVERVIEW
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_subscription(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access subscription information."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    subscription = (
        Subscription.objects
        .select_related("plan")
        .filter(
            tenant=tenant
        )
        .first()
    )

    if not subscription:
        return Response({
            "message":
                "No subscription was found for this business."
        }, status=404)

    plan = subscription.plan

    # --------------------------------------------------------
    # Usage
    # --------------------------------------------------------

    used_users = User.objects.filter(
        tenant=tenant
    ).exclude(
        role="platform_admin"
    ).count()

    used_documents = Document.objects.filter(
        tenant=tenant
    ).count()

    used_print_jobs = PrintJob.objects.filter(
        tenant=tenant
    ).count()

    total_storage_bytes = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .aggregate(
            total=Sum("size")
        )["total"]
        or 0
    )

    total_storage_mb = (
        Decimal(total_storage_bytes)
        / Decimal(1024 * 1024)
    )

    # --------------------------------------------------------
    # Remaining days
    # --------------------------------------------------------

    days_remaining = None

    if subscription.current_period_end:
        difference = (
            subscription.current_period_end
            - timezone.now()
        )

        days_remaining = max(
            difference.days,
            0
        )

    trial_days_remaining = None

    if subscription.trial_end:
        difference = (
            subscription.trial_end
            - timezone.now()
        )

        trial_days_remaining = max(
            difference.days,
            0
        )

    # --------------------------------------------------------
    # Payment history
    # --------------------------------------------------------

    payments = (
        SubscriptionPayment.objects
        .filter(
            tenant=tenant,
            subscription=subscription
        )
        .order_by(
            "-created_at"
        )[:20]
    )

    payments_data = []

    for payment in payments:

        payments_data.append({
            "id":
                payment.id,

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "payment_method":
                payment.payment_method,

            "phone_number":
                payment.phone_number,

            "status":
                payment.status,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "checkout_request_id":
                payment.checkout_request_id,

            "provider_reference":
                payment.provider_reference,

            "period_start":
                payment.period_start,

            "period_end":
                payment.period_end,

            "paid_at":
                payment.paid_at,

            "created_at":
                payment.created_at,
        })

    # --------------------------------------------------------
    # Available plans
    # --------------------------------------------------------

    available_plans = (
        Plan.objects
        .filter(
            is_active=True
        )
        .order_by(
            "monthly_price"
        )
    )

    plan_data = []

    for item in available_plans:

        plan_data.append({
            "id":
                item.id,

            "name":
                item.name,

            "slug":
                item.slug,

            "description":
                item.description,

            "monthly_price":
                item.monthly_price,

            "yearly_price":
                item.yearly_price,

            "max_users":
                item.max_users,

            "max_documents":
                item.max_documents,

            "max_print_jobs":
                item.max_print_jobs,

            "max_storage_mb":
                item.max_storage_mb,

            "allow_color_printing":
                item.allow_color_printing,

            "allow_double_sided":
                item.allow_double_sided,

            "allow_multiple_printers":
                item.allow_multiple_printers,

            "allow_staff_accounts":
                item.allow_staff_accounts,

            "allow_custom_domain":
                item.allow_custom_domain,

            "advanced_reports":
                item.advanced_reports,

            "api_access":
                item.api_access,

            "priority_support":
                item.priority_support,

            "is_popular":
                item.is_popular,
        })

    return Response({
        "success": True,

        "subscription": {
            "id":
                subscription.id,

            "status":
                subscription.status,

            "billing_cycle":
                subscription.billing_cycle,

            "start_date":
                subscription.start_date,

            "current_period_start":
                subscription.current_period_start,

            "current_period_end":
                subscription.current_period_end,

            "trial_start":
                subscription.trial_start,

            "trial_end":
                subscription.trial_end,

            "days_remaining":
                days_remaining,

            "trial_days_remaining":
                trial_days_remaining,

            "auto_renew":
                subscription.auto_renew,

            "payment_method":
                subscription.payment_method,

            "plan": {
                "id":
                    plan.id,

                "name":
                    plan.name,

                "slug":
                    plan.slug,

                "description":
                    plan.description,

                "monthly_price":
                    plan.monthly_price,

                "yearly_price":
                    plan.yearly_price,

                "max_users":
                    plan.max_users,

                "max_documents":
                    plan.max_documents,

                "max_print_jobs":
                    plan.max_print_jobs,

                "max_storage_mb":
                    plan.max_storage_mb,
            }
        },

        "usage": {
            "users": {
                "used":
                    used_users,

                "limit":
                    plan.max_users,
            },

            "documents": {
                "used":
                    used_documents,

                "limit":
                    plan.max_documents,
            },

            "print_jobs": {
                "used":
                    used_print_jobs,

                "limit":
                    plan.max_print_jobs,
            },

            "storage": {
                "used_mb":
                    round(
                        float(
                            total_storage_mb
                        ),
                        2
                    ),

                "limit_mb":
                    plan.max_storage_mb,
            }
        },

        "payments":
            payments_data,

        "available_plans":
            plan_data,
    })


# ============================================================
# CHANGE PLAN
# ============================================================




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_business_plan(request):

    user = request.user

    # ---------------------------------------------------------
    # Permission
    # ---------------------------------------------------------

    if user.role != "business_admin":
        return Response(
            {
                "success": False,
                "message":
                    "Only the business administrator can change subscription plans.",
            },
            status=403,
        )

    tenant = user.tenant

    if not tenant:
        return Response(
            {
                "success": False,
                "message":
                    "Your account is not linked to a business.",
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Subscription
    # ---------------------------------------------------------

    subscription = (
        Subscription.objects
        .select_related("plan")
        .filter(
            tenant=tenant
        )
        .first()
    )

    if not subscription:
        return Response(
            {
                "success": False,
                "message":
                    "Subscription not found.",
            },
            status=404,
        )

    # ---------------------------------------------------------
    # Request data
    # ---------------------------------------------------------

    plan_id = request.data.get(
        "plan_id"
    )

    billing_cycle = request.data.get(
        "billing_cycle",
        subscription.billing_cycle,
    )

    phone_number = request.data.get(
        "phone_number"
    )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    if not plan_id:
        return Response(
            {
                "success": False,
                "message":
                    "Please select a subscription plan.",
            },
            status=400,
        )

    if billing_cycle not in [
        "monthly",
        "yearly",
    ]:
        return Response(
            {
                "success": False,
                "message":
                    "Billing cycle must be monthly or yearly.",
            },
            status=400,
        )

    if not phone_number:
        return Response(
            {
                "success": False,
                "message":
                    "M-Pesa phone number is required.",
            },
            status=400,
        )

    try:
        normalized_phone = (
            normalize_mpesa_phone(
                phone_number
            )
        )

    except ValueError as error:
        return Response(
            {
                "success": False,
                "message": str(error),
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Find plan
    # ---------------------------------------------------------

    plan = Plan.objects.filter(
        id=plan_id,
        is_active=True,
    ).first()

    if not plan:
        return Response(
            {
                "success": False,
                "message":
                    "Selected plan was not found.",
            },
            status=404,
        )

    # ---------------------------------------------------------
    # Same subscription check
    # ---------------------------------------------------------

    if (
        subscription.status == "active"
        and
        plan.id == subscription.plan_id
        and
        billing_cycle ==
            subscription.billing_cycle
    ):
        return Response(
            {
                "success": False,
                "message":
                    "You are already using this plan and billing cycle.",
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Determine amount
    # ---------------------------------------------------------

    amount = (
        plan.monthly_price
        if billing_cycle == "monthly"
        else plan.yearly_price
    )

    if amount is None:
        return Response(
            {
                "success": False,
                "message":
                    "Price has not been configured for this billing cycle.",
            },
            status=400,
        )

    amount = Decimal(str(amount))

    if amount <= 0:
        return Response(
            {
                "success": False,
                "message":
                    "Invalid subscription price.",
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Create pending payment
    # ---------------------------------------------------------

    payment = SubscriptionPayment.objects.create(

        subscription=subscription,

        tenant=tenant,

        pending_plan=plan,

        billing_cycle=billing_cycle,

        amount=amount,

        currency="KES",

        payment_method="m-pesa",

        phone_number=normalized_phone,

        status="pending",
    )

    # ---------------------------------------------------------
    # Initiate Daraja STK push
    # ---------------------------------------------------------

    try:

        mpesa_response = initiate_stk_push(

            phone_number=
                normalized_phone,

            amount=
                amount,

            account_reference=
                f"PF-{payment.id}",

            description=
                f"{plan.name} subscription",
        )

    except requests.RequestException as error:

        payment.status = "failed"

        payment.provider_reference = (
            str(error)[:255]
        )

        payment.save(
            update_fields=[
                "status",
                "provider_reference",
            ]
        )

        return Response(
            {
                "success": False,
                "message":
                    "Unable to connect to M-Pesa. Please try again.",
            },
            status=502,
        )

    except Exception as error:

        payment.status = "failed"

        payment.provider_reference = (
            str(error)[:255]
        )

        payment.save(
            update_fields=[
                "status",
                "provider_reference",
            ]
        )

        return Response(
            {
                "success": False,
                "message":
                    "Unable to initiate M-Pesa payment.",
            },
            status=500,
        )

    # ---------------------------------------------------------
    # Validate Daraja response
    # ---------------------------------------------------------

    response_code = str(
        mpesa_response.get(
            "ResponseCode",
            ""
        )
    )

    if response_code != "0":

        payment.status = "failed"

        payment.provider_reference = (
            mpesa_response.get(
                "errorMessage"
            )
            or
            mpesa_response.get(
                "ResponseDescription"
            )
            or
            "STK Push request rejected."
        )

        payment.save(
            update_fields=[
                "status",
                "provider_reference",
            ]
        )

        return Response(
            {
                "success": False,
                "message":
                    payment.provider_reference,
            },
            status=400,
        )

    # ---------------------------------------------------------
    # Save M-Pesa identifiers
    # ---------------------------------------------------------

    payment.checkout_request_id = (
        mpesa_response.get(
            "CheckoutRequestID"
        )
    )

    payment.provider_reference = (
        mpesa_response.get(
            "MerchantRequestID"
        )
    )

    payment.save(
        update_fields=[
            "checkout_request_id",
            "provider_reference",
        ]
    )

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return Response(
        {
            "success": True,

            "message":
                "M-Pesa payment request sent. Enter your M-Pesa PIN on your phone.",

            "payment": {
                "id":
                    payment.id,

                "amount":
                    payment.amount,

                "currency":
                    payment.currency,

                "phone_number":
                    payment.phone_number,

                "status":
                    payment.status,

                "checkout_request_id":
                    payment.checkout_request_id,
            },

            "pending_plan": {
                "id":
                    plan.id,

                "name":
                    plan.name,

                "slug":
                    plan.slug,

                "billing_cycle":
                    billing_cycle,

                "amount":
                    amount,
            },

            "mpesa": {
                "merchant_request_id":
                    mpesa_response.get(
                        "MerchantRequestID"
                    ),

                "checkout_request_id":
                    mpesa_response.get(
                        "CheckoutRequestID"
                    ),

                "response_description":
                    mpesa_response.get(
                        "ResponseDescription"
                    ),

                "customer_message":
                    mpesa_response.get(
                        "CustomerMessage"
                    ),
            },
        },
        status=201,
    )






@api_view(["POST"])
@permission_classes([AllowAny])
def subscription_mpesa_callback(request):

    print("\n")
    print("=" * 70)
    print("M-PESA SUBSCRIPTION CALLBACK RECEIVED")
    print("=" * 70)
    print(request.data)
    print("=" * 70)
    print("\n")

    callback = (
        request.data
        .get("Body", {})
        .get("stkCallback", {})
    )

    checkout_request_id = callback.get(
        "CheckoutRequestID"
    )

    result_code = callback.get(
        "ResultCode"
    )

    result_description = callback.get(
        "ResultDesc",
        ""
    )

    print(
        "CheckoutRequestID:",
        checkout_request_id
    )

    print(
        "ResultCode:",
        result_code
    )

    print(
        "ResultDesc:",
        result_description
    )

    # ---------------------------------------------------------
    # Validate callback
    # ---------------------------------------------------------

    if not checkout_request_id:
        return Response(
            {
                "ResultCode": 0,
                "ResultDesc":
                    "Callback received.",
            }
        )

    # ---------------------------------------------------------
    # Get callback metadata
    # ---------------------------------------------------------

    metadata_items = (
        callback
        .get("CallbackMetadata", {})
        .get("Item", [])
    )

    metadata = {}

    for item in metadata_items:

        name = item.get("Name")

        if not name:
            continue

        metadata[name] = item.get(
            "Value"
        )

    print(
        "Callback Metadata:",
        metadata
    )

    # ---------------------------------------------------------
    # Process transaction
    # ---------------------------------------------------------

    with transaction.atomic():

        payment = (
            SubscriptionPayment.objects

            # Lock ONLY the SubscriptionPayment row.
            # This avoids:
            # FOR UPDATE cannot be applied to the
            # nullable side of an outer join.
            .select_for_update(
                of=("self",)
            )

            .select_related(
                "subscription",
                "pending_plan",
                "tenant",
            )

            .filter(
                checkout_request_id=
                    checkout_request_id
            )

            .first()
        )

        # -----------------------------------------------------
        # Payment not found
        # -----------------------------------------------------

        if not payment:

            print(
                "PAYMENT NOT FOUND FOR CALLBACK:",
                checkout_request_id
            )

            # Safaricom should still receive HTTP 200
            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Callback acknowledged.",
                }
            )

        print(
            "Payment found:",
            payment.id
        )

        # -----------------------------------------------------
        # Idempotency
        # -----------------------------------------------------

        if payment.status == "paid":

            print(
                "PAYMENT ALREADY PROCESSED:",
                payment.id
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Payment already processed.",
                }
            )

        # -----------------------------------------------------
        # Handle failed / cancelled payment
        # -----------------------------------------------------

        try:
            mpesa_result_code = int(
                result_code
            )
        except (
            TypeError,
            ValueError,
        ):
            mpesa_result_code = -1

        if mpesa_result_code != 0:

            print(
                "M-PESA PAYMENT FAILED:",
                result_description
            )

            payment.status = "failed"

            payment.provider_reference = (
                result_description[:255]
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                ]
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Failed payment recorded.",
                }
            )

        # -----------------------------------------------------
        # Successful payment metadata
        # -----------------------------------------------------

        receipt = metadata.get(
            "MpesaReceiptNumber"
        )

        mpesa_amount = metadata.get(
            "Amount"
        )

        phone_number = metadata.get(
            "PhoneNumber"
        )

        transaction_date = metadata.get(
            "TransactionDate"
        )

        print(
            "M-Pesa Receipt:",
            receipt
        )

        print(
            "M-Pesa Amount:",
            mpesa_amount
        )

        print(
            "M-Pesa Phone:",
            phone_number
        )

        print(
            "M-Pesa Transaction Date:",
            transaction_date
        )

        # -----------------------------------------------------
        # Validate receipt
        # -----------------------------------------------------

        if not receipt:

            print(
                "SUCCESS CALLBACK HAS NO RECEIPT NUMBER"
            )

            payment.status = "failed"

            payment.provider_reference = (
                "Successful M-Pesa callback "
                "did not include a receipt number."
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                ]
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Missing M-Pesa receipt recorded.",
                }
            )

        # -----------------------------------------------------
        # Verify payment amount
        # -----------------------------------------------------

        if mpesa_amount is not None:

            try:

                callback_amount = Decimal(
                    str(mpesa_amount)
                )

                expected_amount = Decimal(
                    str(payment.amount)
                )

            except Exception:

                payment.status = "failed"

                payment.provider_reference = (
                    "Invalid amount received "
                    "from M-Pesa callback."
                )

                payment.save(
                    update_fields=[
                        "status",
                        "provider_reference",
                    ]
                )

                return Response(
                    {
                        "ResultCode": 0,
                        "ResultDesc":
                            "Invalid callback amount.",
                    }
                )

            if callback_amount != expected_amount:

                print(
                    "AMOUNT MISMATCH"
                )

                print(
                    "Expected:",
                    expected_amount
                )

                print(
                    "Received:",
                    callback_amount
                )

                payment.status = "failed"

                payment.provider_reference = (
                    "M-Pesa callback amount mismatch."
                )

                payment.save(
                    update_fields=[
                        "status",
                        "provider_reference",
                    ]
                )

                return Response(
                    {
                        "ResultCode": 0,
                        "ResultDesc":
                            "Amount mismatch recorded.",
                    }
                )

        # -----------------------------------------------------
        # Get subscription and selected plan
        # -----------------------------------------------------

        subscription = payment.subscription

        plan = payment.pending_plan

        if not subscription:

            print(
                "SUBSCRIPTION NOT FOUND FOR PAYMENT:",
                payment.id
            )

            payment.status = "failed"

            payment.provider_reference = (
                "Subscription not found."
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                ]
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Subscription not found.",
                }
            )

        if not plan:

            print(
                "PENDING PLAN NOT FOUND:",
                payment.id
            )

            payment.status = "failed"

            payment.provider_reference = (
                "Pending subscription plan not found."
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                ]
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Missing pending plan.",
                }
            )

        # -----------------------------------------------------
        # Validate billing cycle
        # -----------------------------------------------------

        if payment.billing_cycle not in [
            "monthly",
            "yearly",
        ]:

            print(
                "INVALID BILLING CYCLE:",
                payment.billing_cycle
            )

            payment.status = "failed"

            payment.provider_reference = (
                "Invalid subscription billing cycle."
            )

            payment.save(
                update_fields=[
                    "status",
                    "provider_reference",
                ]
            )

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                        "Invalid billing cycle.",
                }
            )

        # -----------------------------------------------------
        # Calculate subscription period
        # -----------------------------------------------------

        now = timezone.now()

        period_start = now

        if payment.billing_cycle == "yearly":

            period_end = (
                period_start
                + relativedelta(
                    years=1
                )
            )

        else:

            period_end = (
                period_start
                + relativedelta(
                    months=1
                )
            )

        # -----------------------------------------------------
        # Update subscription
        # -----------------------------------------------------

        subscription.plan = plan

        subscription.billing_cycle = (
            payment.billing_cycle
        )

        subscription.status = "active"

        subscription.start_date = (
            subscription.start_date
            or now
        )

        subscription.current_period_start = (
            period_start
        )

        subscription.current_period_end = (
            period_end
        )

        subscription.payment_method = (
            "m-pesa"
        )

        subscription.save(
            update_fields=[
                "plan",
                "billing_cycle",
                "status",
                "start_date",
                "current_period_start",
                "current_period_end",
                "payment_method",
                "updated_at",
            ]
        )

        print(
            "SUBSCRIPTION ACTIVATED"
        )

        print(
            "Plan:",
            plan.name
        )

        print(
            "Billing cycle:",
            payment.billing_cycle
        )

        print(
            "Period start:",
            period_start
        )

        print(
            "Period end:",
            period_end
        )

        # -----------------------------------------------------
        # Update payment
        # -----------------------------------------------------

        payment.status = "paid"

        payment.mpesa_receipt_number = (
            receipt
        )

        payment.transaction_id = (
            receipt
        )

        if phone_number:
            payment.phone_number = str(
                phone_number
            )

        payment.paid_at = now

        payment.period_start = (
            period_start
        )

        payment.period_end = (
            period_end
        )

        payment.save(
            update_fields=[
                "status",
                "mpesa_receipt_number",
                "transaction_id",
                "phone_number",
                "paid_at",
                "period_start",
                "period_end",
            ]
        )

        print(
            "PAYMENT MARKED AS PAID:",
            payment.id
        )

        print(
            "M-PESA RECEIPT:",
            payment.mpesa_receipt_number
        )

    # ---------------------------------------------------------
    # Safaricom response
    # ---------------------------------------------------------

    return Response(
        {
            "ResultCode": 0,
            "ResultDesc":
                "Subscription payment processed successfully.",
        }
    )




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_payment_status(
    request,
    payment_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response(
            {
                "message":
                    "Not allowed.",
            },
            status=403,
        )

    tenant = user.tenant

    payment = (
        SubscriptionPayment.objects
        .filter(
            id=payment_id,
            tenant=tenant,
        )
        .first()
    )

    if not payment:
        return Response(
            {
                "message":
                    "Payment not found.",
            },
            status=404,
        )

    return Response(
        {
            "success": True,

            "payment": {
                "id":
                    payment.id,

                "status":
                    payment.status,

                "amount":
                    payment.amount,

                "mpesa_receipt_number":
                    payment.mpesa_receipt_number,

                "checkout_request_id":
                    payment.checkout_request_id,

                "paid_at":
                    payment.paid_at,
            }
        }
    )






# ============================================================
# AUTO RENEW
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_subscription_auto_renew(request):

    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator can change auto-renew settings."
        }, status=403)

    tenant = user.tenant

    subscription = Subscription.objects.filter(
        tenant=tenant
    ).first()

    if not subscription:
        return Response({
            "message":
                "Subscription not found."
        }, status=404)

    auto_renew = request.data.get(
        "auto_renew"
    )

    if not isinstance(
        auto_renew,
        bool
    ):
        return Response({
            "message":
                "auto_renew must be true or false."
        }, status=400)

    subscription.auto_renew = auto_renew

    subscription.save(
        update_fields=[
            "auto_renew",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Auto-renew setting updated successfully.",

        "auto_renew":
            subscription.auto_renew,
    })




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_subscription_status(
    request
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response(
            {
                "message":
                    "Not allowed."
            },
            status=403,
        )

    tenant = user.tenant

    if not tenant:
        return Response(
            {
                "message":
                    "Business not found."
            },
            status=404,
        )

    state = (
        get_subscription_state(
            tenant
        )
    )

    subscription = state[
        "subscription"
    ]

    if not subscription:
        return Response(
            {
                "success": True,
                "has_subscription":
                    False,
                "is_active":
                    False,
                "is_expired":
                    False,
                "subscription":
                    None,
                "plan":
                    None,
                "usage":
                    None,
            }
        )

    plan = subscription.plan

    # ---------------------------------------
    # Usage
    # ---------------------------------------

    users_count = (
        User.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    documents_count = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    print_jobs_count = (
        PrintJob.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    storage_bytes = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .aggregate(
            total=Sum("size")
        )
        .get("total")
        or 0
    )

    storage_mb = round(
        storage_bytes /
        (1024 * 1024),
        2,
    )

    return Response(
        {
            "success": True,

            "has_subscription":
                state[
                    "has_subscription"
                ],

            "is_active":
                state[
                    "is_active"
                ],

            "is_expired":
                state[
                    "is_expired"
                ],

            "subscription": {
                "id":
                    subscription.id,

                "status":
                    subscription.status,

                "billing_cycle":
                    subscription.billing_cycle,

                "current_period_start":
                    subscription.current_period_start,

                "current_period_end":
                    subscription.current_period_end,
            },

            "plan": {
                "id":
                    plan.id,

                "name":
                    plan.name,

                "slug":
                    plan.slug,

                "max_users":
                    plan.max_users,

                "max_documents":
                    plan.max_documents,

                "max_print_jobs":
                    plan.max_print_jobs,

                "max_storage_mb":
                    plan.max_storage_mb,

                "allow_color_printing":
                    plan.allow_color_printing,

                "allow_double_sided":
                    plan.allow_double_sided,

                "allow_multiple_printers":
                    plan.allow_multiple_printers,

                "allow_staff_accounts":
                    plan.allow_staff_accounts,

                "allow_custom_domain":
                    plan.allow_custom_domain,

                "advanced_reports":
                    plan.advanced_reports,

                "api_access":
                    plan.api_access,

                "priority_support":
                    plan.priority_support,
            },

            "usage": {
                "users":
                    users_count,

                "documents":
                    documents_count,

                "print_jobs":
                    print_jobs_count,

                "storage_mb":
                    storage_mb,
            },
        }
    )