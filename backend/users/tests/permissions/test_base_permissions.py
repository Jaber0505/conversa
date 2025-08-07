import pytest
from rest_framework.permissions import SAFE_METHODS
from rest_framework.test import APIRequestFactory

from users.permissions.base import (
    IsSelf,
    IsSelfOrReadOnly,
    IsAdminOrReadOnly,
    IsAuthenticatedAndActive
)


@pytest.fixture
def factory():
    return APIRequestFactory()


def make_request(factory, method, user):
    return factory.generic(method=method, path="/fake-endpoint", HTTP_AUTHORIZATION="", user=user)


# === IsSelf ===

def test_is_self_grants_permission_when_same_user(factory, user):
    request = make_request(factory, "GET", user)
    permission = IsSelf()
    assert permission.has_object_permission(request, None, user)


def test_is_self_denies_permission_when_different_user(factory, user, superuser):
    request = make_request(factory, "GET", user)
    permission = IsSelf()
    assert not permission.has_object_permission(request, None, superuser)


# === IsSelfOrReadOnly ===

@pytest.mark.parametrize("method", SAFE_METHODS)
def test_is_self_or_read_only_allows_safe_methods(factory, user, superuser, method):
    request = make_request(factory, method, user)
    permission = IsSelfOrReadOnly()
    assert permission.has_object_permission(request, None, superuser)


def test_is_self_or_read_only_allows_write_if_self(factory, user):
    request = make_request(factory, "PATCH", user)
    permission = IsSelfOrReadOnly()
    assert permission.has_object_permission(request, None, user)


def test_is_self_or_read_only_denies_write_if_not_self(factory, user, superuser):
    request = make_request(factory, "PUT", user)
    permission = IsSelfOrReadOnly()
    assert not permission.has_object_permission(request, None, superuser)


# === IsAdminOrReadOnly ===

@pytest.mark.parametrize("method", SAFE_METHODS)
def test_is_admin_or_read_only_allows_safe_methods(factory, user, method):
    request = make_request(factory, method, user)
    permission = IsAdminOrReadOnly()
    assert permission.has_permission(request, None)


def test_is_admin_or_read_only_allows_write_if_admin(factory, superuser):
    request = make_request(factory, "POST", superuser)
    permission = IsAdminOrReadOnly()
    assert permission.has_permission(request, None)


def test_is_admin_or_read_only_denies_write_if_not_admin(factory, user):
    request = make_request(factory, "DELETE", user)
    permission = IsAdminOrReadOnly()
    assert not permission.has_permission(request, None)


# === IsAuthenticatedAndActive ===

def test_is_authenticated_and_active_grants_if_authenticated(factory, user):
    request = make_request(factory, "GET", user)
    permission = IsAuthenticatedAndActive()
    assert permission.has_permission(request, None)


def test_is_authenticated_and_active_denies_if_not_authenticated(factory):
    anonymous_user = type("Anonymous", (), {"is_authenticated": False, "is_active": True})()
    request = make_request(factory, "GET", anonymous_user)
    permission = IsAuthenticatedAndActive()
    assert not permission.has_permission(request, None)


def test_is_authenticated_and_active_denies_if_inactive(factory, user):
    user.is_active = False
    request = make_request(factory, "GET", user)
    permission = IsAuthenticatedAndActive()
    assert not permission.has_permission(request, None)
