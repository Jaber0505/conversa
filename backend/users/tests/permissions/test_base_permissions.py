import pytest
from rest_framework.permissions import SAFE_METHODS
from users.permissions import IsSelf, IsSelfOrReadOnly, IsAdminOrReadOnly


@pytest.fixture
def fake_request(rf, user):
    request = rf.get("/")
    request.user = user
    return request


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        email="other@example.com", password="pass"
    )


# ============================================================================
# IsSelf
# ============================================================================

def test_is_self_allows_own_resource(fake_request, user):
    permission = IsSelf()
    assert permission.has_object_permission(fake_request, None, user) is True


def test_is_self_denies_other_resource(fake_request, other_user):
    permission = IsSelf()
    assert permission.has_object_permission(fake_request, None, other_user) is False


# ============================================================================
# IsSelfOrReadOnly
# ============================================================================

@pytest.mark.parametrize("method", SAFE_METHODS)
def test_is_self_or_read_only_allows_safe_methods(method, rf, user, other_user):
    request = rf.get("/", REQUEST_METHOD=method)
    request.user = user
    permission = IsSelfOrReadOnly()
    assert permission.has_object_permission(request, None, other_user) is True


def test_is_self_or_read_only_allows_update_own_resource(rf, user):
    request = rf.put("/", REQUEST_METHOD="PUT")
    request.user = user
    permission = IsSelfOrReadOnly()
    assert permission.has_object_permission(request, None, user) is True


def test_is_self_or_read_only_denies_update_other_resource(rf, user, other_user):
    request = rf.patch("/", REQUEST_METHOD="PATCH")
    request.user = user
    permission = IsSelfOrReadOnly()
    assert permission.has_object_permission(request, None, other_user) is False


# ============================================================================
# IsAdminOrReadOnly
# ============================================================================

@pytest.mark.parametrize("method", SAFE_METHODS)
def test_is_admin_or_read_only_allows_safe_methods(method, rf, user):
    request = rf.get("/", REQUEST_METHOD=method)
    request.user = user
    permission = IsAdminOrReadOnly()
    assert permission.has_permission(request, None) is True


def test_is_admin_or_read_only_allows_admin_edit(rf, user):
    user.is_staff = True
    request = rf.post("/", REQUEST_METHOD="POST")
    request.user = user
    permission = IsAdminOrReadOnly()
    assert permission.has_permission(request, None) is True


def test_is_admin_or_read_only_denies_non_admin_edit(rf, user):
    request = rf.post("/", REQUEST_METHOD="POST")
    request.user = user
    permission = IsAdminOrReadOnly()
    assert permission.has_permission(request, None) is False
