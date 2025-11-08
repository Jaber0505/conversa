from django.urls import path
from .views import CreateCheckoutSessionView, StripeWebhookView

app_name = "payments"

urlpatterns = [
    path(
        "checkout-session/",
        CreateCheckoutSessionView.as_view(),
        name="create-checkout-session",
    ),
    path("stripe-webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
