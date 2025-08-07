from rest_framework.throttling import AnonRateThrottle

class PasswordResetThrottle(AnonRateThrottle):
    scope = "reset_password"
