from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        # Check if the user is a manager
        return request.user.groups.filter(name='Managers').exists()

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name="DeliveryCrew").exists()

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        # Is a customer if the authenticated user is not in a group
        return request.user.groups.count() == 0

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.groups.filter(name='Managers').exists()
