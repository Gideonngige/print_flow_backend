# serializers.py

from rest_framework import serializers
from .common_imports import *


class PublicPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan

        fields = [
            "id",
            "name",
            "slug",
            "description",

            "monthly_price",
            "yearly_price",

            "max_users",
            "max_documents",
            "max_print_jobs",
            "max_storage_mb",

            "allow_color_printing",
            "allow_double_sided",
            "allow_multiple_printers",
            "allow_staff_accounts",

            "allow_custom_domain",
            "advanced_reports",
            "api_access",
            "priority_support",

            "is_popular",
            "is_active",
        ]