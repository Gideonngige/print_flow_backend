# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum, Q
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string

# REST framework imports
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status

# Third-party imports
import cloudinary.uploader
import requests
import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

import secrets

# Local imports
from print_flow_app.models import User, Document, PrintJob, Payment

# Logging
import logging
logger = logging.getLogger("backend")

# System
import os

from django.conf import settings

# signup
import uuid

# sign in
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

import os
import resend
import traceback

from django.utils.html import escape


import os
import cloudinary.uploader

from PyPDF2 import PdfReader
from django.core.files.base import ContentFile
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
