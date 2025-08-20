from django.urls import path
from .views import CreateCheckoutSessionView, StripeWebhookView

urlpatterns = [
    path("checkout-session/", CreateCheckoutSessionView.as_view(), name="payments-checkout-session"),
    path("stripe-webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
