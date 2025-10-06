
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "hubinsight.pagination.RoleAwarePageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Insight Hub API",
    "DESCRIPTION": "Task scheduling & execution APIs",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,

    "CONTACT": {"name": "Platform Team", "email": "ops@example.com"},
    "LICENSE": {"name": "Proprietary"},
    "EXTERNAL_DOCS": {"description": "Team Wiki", "url": "https://wiki.example.com"},

    "SECURITY": [{"bearerAuth": []}],  # JWT Bearer
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True, "displayRequestDuration": True},
    "REDOC_SETTINGS": {"expandResponses": "200,201,400,401,403,404"},

    "COMPONENT_SPLIT_REQUEST": True,   
    "SORT_OPERATIONS": True,
    "SCHEMA_PATH_PREFIX": r"/api",    
}
