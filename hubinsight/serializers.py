import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PredefinedTask, Schedule, Execution
from .validators import validate_inputs
from .services import validate_cron_5_detailed, compute_next_run_at

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
        ]

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(pwd)
        user.save()
        # logging
        actor = getattr(self.context.get("request"), "user", None)
        logger.info(
            "user_created",
            extra={"new_user": user.id, "by": getattr(actor, "id", None)},
        )
        return user


class PredefinedTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredefinedTask
        fields = ["id", "name", "description", "inputs_schema", "is_schedulable"]


class ScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ["id", "task", "cron_expression", "inputs", "status"]

    def validate(self, attrs):
        task = attrs.get("task")
        cron = attrs.get("cron_expression")
        inputs = attrs.get("inputs", {})

        ok, msg = validate_cron_5_detailed(cron)
        if not ok:
            logger.warning("schedule_create_invalid_cron", extra={"cron": cron})
            raise serializers.ValidationError({"cron_expression": msg})

        if not task or not task.is_schedulable:
            logger.warning(
                "schedule_create_invalid_task",
                extra={"task": getattr(task, "id", None)},
            )
            raise serializers.ValidationError({"task": "This task is not schedulable."})

        errs = validate_inputs(task.inputs_schema, inputs or {})
        if errs:
            logger.warning("schedule_create_invalid_inputs", extra={"task": task.id, "errors_count": len(errs)})
            raise serializers.ValidationError({"inputs": errs})

        user = self.context["request"].user
        new_status = attrs.get("status", Schedule.Status.ENABLED)
        if not user.is_superuser and new_status == Schedule.Status.ENABLED:
            active_count = Schedule.objects.filter(
                owner=user, status=Schedule.Status.ENABLED, deleted_at__isnull=True
            ).count()
            if active_count >= 5:
                logger.warning("schedule_create_rate_limited", extra={"owner": user.id, "active_count": active_count})
                raise serializers.ValidationError("You can not have more than 5 active jobs.")

        return attrs

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        validated_data["next_run_at"] = compute_next_run_at(validated_data["cron_expression"])
        obj = super().create(validated_data)
        logger.info(
            "schedule_created",
            extra={
                "schedule_id": obj.id,
                "owner": obj.owner_id,
                "task": obj.task_id,
                "status": obj.status,
            },
        )
        return obj


class ScheduleSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.name", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "task",
            "task_name",
            "owner",
            "owner_username",
            "cron_expression",
            "inputs",
            "status",
            "created_at",
            "last_run_at",
            "next_run_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "last_run_at", "next_run_at", "deleted_at"]


class ScheduleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ["cron_expression", "inputs", "status"]

    def validate(self, attrs):
        sch: Schedule = self.instance
        cron = attrs.get("cron_expression", sch.cron_expression)
        inputs = attrs.get("inputs", sch.inputs)

        ok, msg = validate_cron_5_detailed(cron)
        if not ok:
            logger.warning("schedule_update_invalid_cron", extra={"schedule_id": sch.id, "cron": cron})
            raise serializers.ValidationError({"cron_expression": msg})

        errs = validate_inputs(sch.task.inputs_schema, inputs or {})
        if errs:
            logger.warning("schedule_update_invalid_inputs", extra={"schedule_id": sch.id, "errors_count": len(errs)})
            raise serializers.ValidationError({"inputs": errs})

        new_status = attrs.get("status", sch.status)
        user = self.context["request"].user
        if not user.is_superuser and new_status == Schedule.Status.ENABLED:
            active_count = Schedule.objects.filter(
                owner=user, status=Schedule.Status.ENABLED, deleted_at__isnull=True
            ).exclude(pk=sch.pk).count()
            if active_count >= 5:
                logger.warning("schedule_update_rate_limited", extra={"owner": user.id, "active_count": active_count})
                raise serializers.ValidationError("You can not have more than 5 active jobs.")

        return attrs

    def update(self, instance, validated_data):
        instance.cron_expression = validated_data.get("cron_expression", instance.cron_expression)
        instance.inputs = validated_data.get("inputs", instance.inputs)
        instance.status = validated_data.get("status", instance.status)
        instance.next_run_at = compute_next_run_at(instance.cron_expression)
        instance.save(update_fields=["cron_expression", "inputs", "status", "next_run_at"])
        logger.info(
            "schedule_updated",
            extra={"schedule_id": instance.id, "status": instance.status},
        )
        return instance


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = ["id", "schedule", "task_name", "started_at", "finished_at", "status", "runtime_ms", "logs"]
