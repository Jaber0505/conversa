# backend/payments/urls.py
from django.urls import path
from .views import CreateIntentView, StripeWebhookView

urlpatterns = [
    path("create-intent/", CreateIntentView.as_view(), name="payments-create-intent"),
    path("stripe-webhook/", StripeWebhookView.as_view(), name="payments-stripe-webhook"),
]
