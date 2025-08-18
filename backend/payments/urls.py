# payments/urls.py
from django.urls import path
from payments.views import CreateIntentView, StripeWebhookView, ConfirmSimulatorView, StripeConfigView
from django.conf import settings

urlpatterns = [
    path("config/", StripeConfigView.as_view(), name="stripe-config"),
    path("create-intent/", CreateIntentView.as_view(), name="payments-create-intent"),   # réel (front)
    path("stripe-webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),         # réel (webhook)
]

# Route simulateur visible uniquement en dev/test (DEBUG=True)
if getattr(settings, "DEBUG", False):
    urlpatterns += [
        path("sim/confirm/", ConfirmSimulatorView.as_view(), name="payments-confirm-simulator"),  # simulateur (.http)
    ]
