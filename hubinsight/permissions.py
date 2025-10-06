from rest_framework.permissions import BasePermission

class IsSuperOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        owner = getattr(obj, "owner", None) or getattr(getattr(obj, "schedule", None), "owner", None)
        return owner == request.user

