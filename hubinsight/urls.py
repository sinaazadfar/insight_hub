from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PredefinedTaskList,
    ScheduleViewSet,
    ExecutionDetail,
    UserCreateView,
)

router = DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedule")

urlpatterns = [
    # Users
    path("users/", UserCreateView.as_view()),

    # Tasks & Schedules
    path("tasks/predefined/", PredefinedTaskList.as_view()),

    # Executions
    path("executions/<int:pk>/", ExecutionDetail.as_view()),

    # Router
    path("", include(router.urls)),
    
    
]
