from rest_framework.pagination import PageNumberPagination

class RoleAwarePageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 10
    def get_page_size(self, request):
        size = super().get_page_size(request)
        if request.user and request.user.is_authenticated and request.user.is_superuser:
            self.max_page_size = 100
        req_size = int(request.query_params.get(self.page_size_query_param, size))
        return min(req_size, self.max_page_size)
