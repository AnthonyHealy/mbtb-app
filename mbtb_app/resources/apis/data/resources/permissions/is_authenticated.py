from rest_framework import permissions, exceptions
from resources.db_operations.user_or_admin import UserOrAdmin
from .base_operations import BaseOperations


# This class is to authenticate admin and user and allow GET requests, block remaining ones.
class IsAuthenticated(permissions.BasePermission):

    # Allow following request from user
    def has_permission(self, request, view):

        # only allow admin's GET request via authorized token
        if request.method == 'GET':
            valid_url = ['brain_dataset', 'other_details', 'get_select_options']

            # splitting url e.g. /brain_dataset/1/ to get brain_dataset for comparison
            url_path = request.path.split('/')
            if max(url_path) in valid_url:
                return self.authenticate(request)

            # deny GET request if url is not in valid_url by default
            return False

        # only allow admin's POST request via authorized token
        if request.method == 'POST':
            valid_url = ['add_new_tissue_requests', 'download_data']

            # splitting url e.g. /brain_dataset/1/ to get brain_dataset for comparison
            url_path = request.path.split('/')
            if max(url_path) in valid_url:
                return self.authenticate(request)

            # deny POST request if url is not in valid_url by default
            return False

        raise exceptions.MethodNotAllowed(method=request.method)

    def authenticate(self, request):
        # Validate request first, obtain response dict containing id and email.
        response = BaseOperations().validate_request(request)

        user = UserOrAdmin(model_name='User').run(id=response['id'], email=response['email'])
        admin = UserOrAdmin(model_name='Admin').run(id=response['id'], email=response['email'])
        if user or admin:
            return True

        return False
