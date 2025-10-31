"""
Base service class for all business logic services.

All service classes should inherit from this base to ensure consistency.
"""

from typing import Any, Dict, Optional
from django.db import transaction


class BaseService:
    """
    Base class for all service layers.

    Services encapsulate business logic and should be the primary way
    to interact with models beyond simple CRUD operations.
    """

    @staticmethod
    def atomic_operation(func):
        """Decorator to wrap service methods in database transactions."""
        def wrapper(*args, **kwargs):
            with transaction.atomic():
                return func(*args, **kwargs)
        return wrapper

    @classmethod
    def validate_and_execute(cls, validation_func, execution_func, *args, **kwargs):
        """
        Execute validation before performing an operation.

        Args:
            validation_func: Function to validate business rules
            execution_func: Function to execute if validation passes
            *args, **kwargs: Arguments to pass to both functions

        Returns:
            Result of execution_func
        """
        validation_func(*args, **kwargs)
        return execution_func(*args, **kwargs)
