import logging
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser

from .models import PredefinedTask, Schedule, Execution
from .serializers import (
    PredefinedTaskSerializer,
    ScheduleCreateSerializer,
    ScheduleSerializer,
    ScheduleUpdateSerializer,
    ExecutionSerializer,
    UserCreateSerializer,
)
from .permissions import IsSuperOrOwner
from .pagination import RoleAwarePageNumberPagination
from .services import ensure_periodic_task

logger = logging.getLogger(__name__)


class PredefinedTaskList(generics.ListAPIView):
    queryset = PredefinedTask.objects.filter(is_schedulable=True).order_by("name")
    serializer_class = PredefinedTaskSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        resp = super().list(request, *args, **kwargs)
        logger.info(
            "predefined_tasks_listed",
            extra={"count": len(resp.data or []), "user": getattr(request.user, "id", None)},
        )
        return resp


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [IsSuperOrOwner]
    pagination_class = RoleAwarePageNumberPagination

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "task", "owner", "created_at", "last_run_at", "next_run_at"]
    ordering_fields = ["created_at", "last_run_at", "next_run_at"]
    search_fields = ["task__name", "owner__username"]

    def get_queryset(self):
        qs = Schedule.objects.filter(deleted_at__isnull=True)
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(owner=user)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ScheduleCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ScheduleUpdateSerializer
        return ScheduleSerializer

    def list(self, request, *args, **kwargs):
        logger.info(
            "schedules_list_requested",
            extra={
                "user": getattr(request.user, "id", None),
                "filters": {k: v for k, v in request.query_params.items()},
            },
        )
        resp = super().list(request, *args, **kwargs)
        logger.info(
            "schedules_list_returned",
            extra={"count": resp.data.get("count", None), "user": getattr(request.user, "id", None)},
        )
        return resp

    def perform_create(self, serializer):
        instance = serializer.save()
        ensure_periodic_task(instance)
        logger.info(
            "schedule_created",
            extra={
                "schedule_id": instance.id,
                "task": instance.task.name if instance.task_id else None,
                "owner": instance.owner_id,
                "status": instance.status,
            },
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        ensure_periodic_task(instance)
        logger.info(
            "schedule_updated",
            extra={
                "schedule_id": instance.id,
                "task": instance.task.name if instance.task_id else None,
                "owner": instance.owner_id,
                "status": instance.status,
            },
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.status = Schedule.Status.DISABLED
        instance.save(update_fields=["deleted_at", "status"])

        from django_celery_beat.models import PeriodicTask

        if instance.beat_periodic_task_id:
            PeriodicTask.objects.filter(id=instance.beat_periodic_task_id).update(enabled=False, args="[]")

        logger.warning(
            "schedule_soft_deleted",
            extra={
                "schedule_id": instance.id,
                "owner": instance.owner_id,
                "beat_task_id": instance.beat_periodic_task_id,
            },
        )

    @action(detail=True, methods=["get"])
    def executions(self, request, pk=None):
        schedule = self.get_object()
        qs = schedule.executions.all()
        page = self.paginate_queryset(qs)
        ser = ExecutionSerializer(page, many=True)
        logger.info(
            "schedule_executions_listed",
            extra={"schedule_id": schedule.id, "count": len(page)},
        )
        return self.get_paginated_response(ser.data)

    @action(detail=False, methods=["post"], url_path="search")
    def advanced_search(self, request):
        allowed_fields = {
            "status",
            "task__name",
            "task__name__icontains",
            "owner__username",
            "created_at",
            "last_run_at",
            "next_run_at",
        }
        filters = request.data.get("filters", {}) or {}
        ordering = request.data.get("ordering", []) or []

        for key in list(filters.keys()):
            if key not in allowed_fields:
                filters.pop(key, None)

        qs = self.get_queryset()
        for k, v in filters.items():
            qs = qs.filter(**{k: v})

        safe_ordering = []
        for f in ordering:
            raw = f.lstrip("-")
            if raw in {fld.split("__")[0] for fld in allowed_fields}:
                safe_ordering.append(f)
        if safe_ordering:
            qs = qs.order_by(*safe_ordering)

        page = self.paginate_queryset(qs)
        ser = ScheduleSerializer(page, many=True)

        logger.info(
            "schedules_advanced_search",
            extra={
                "user": getattr(request.user, "id", None),
                "filters": filters,
                "ordering": safe_ordering,
                "count": len(page),
            },
        )
        return self.get_paginated_response(ser.data)


class ExecutionDetail(generics.RetrieveAPIView):
    queryset = Execution.objects.all()
    serializer_class = ExecutionSerializer
    permission_classes = [IsSuperOrOwner]


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsAdminUser]
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            logger.warning(
                "user_create_forbidden",
                extra={"user": getattr(request.user, "id", None)},
            )
            return Response({"detail": "Only superuser"}, status=403)
        logger.info("user_create_attempt", extra={"by": request.user.id})
        return super().create(request, *args, **kwargs)
