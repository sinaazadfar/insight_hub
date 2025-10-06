from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PredefinedTask, Schedule, Execution
from .validators import validate_inputs
from .services import validate_cron_5_detailed, compute_next_run_at

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "is_superuser",
            "is_active",
        ]
        read_only_fields = ["id", "is_active"]

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(pwd)
        user.save()
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
            raise serializers.ValidationError({"cron_expression": msg})

        if not task or not task.is_schedulable:
            raise serializers.ValidationError({"task": "This task is not schedulable."})

        errs = validate_inputs(task.inputs_schema, inputs or {})
        if errs:
            raise serializers.ValidationError({"inputs": errs})

        user = self.context["request"].user
        new_status = attrs.get("status", Schedule.Status.ENABLED)
        if not user.is_superuser and new_status == Schedule.Status.ENABLED:
            active_count = Schedule.objects.filter(
                owner=user, status=Schedule.Status.ENABLED, deleted_at__isnull=True
            ).count()
            if active_count >= 5:
                raise serializers.ValidationError("You can not have more than 5 active jobs.")

        return attrs

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        validated_data["next_run_at"] = compute_next_run_at(validated_data["cron_expression"])
        return super().create(validated_data)


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
            raise serializers.ValidationError({"cron_expression": msg})

        errs = validate_inputs(sch.task.inputs_schema, inputs or {})
        if errs:
            raise serializers.ValidationError({"inputs": errs})

        new_status = attrs.get("status", sch.status)
        user = self.context["request"].user
        if not user.is_superuser and new_status == Schedule.Status.ENABLED:
            active_count = Schedule.objects.filter(
                owner=user, status=Schedule.Status.ENABLED, deleted_at__isnull=True
            ).exclude(pk=sch.pk).count()
            if active_count >= 5:
                raise serializers.ValidationError("You can not have more than 5 active jobs.")

        return attrs

    def update(self, instance, validated_data):
        instance.cron_expression = validated_data.get("cron_expression", instance.cron_expression)
        instance.inputs = validated_data.get("inputs", instance.inputs)
        instance.status = validated_data.get("status", instance.status)
        instance.next_run_at = compute_next_run_at(instance.cron_expression)
        instance.save(update_fields=["cron_expression", "inputs", "status", "next_run_at"])
        return instance


class ExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Execution
        fields = ["id", "schedule", "task_name", "started_at", "finished_at", "status", "runtime_ms", "logs"]
