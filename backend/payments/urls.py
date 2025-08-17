from django.urls import path
from .views import CreateIntentView, ConfirmIntentView, StripeWebhookView

urlpatterns = [
    path("create-intent/", CreateIntentView.as_view(), name="payments-create-intent"),
    path("confirm/", ConfirmIntentView.as_view(), name="payments-confirm"),  # ← simulateur front
    path("stripe-webhook/", StripeWebhookView.as_view(), name="payments-stripe-webhook"),
]
