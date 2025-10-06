from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PredefinedTask(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    inputs_schema = models.JSONField(default=list)
    is_schedulable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Schedule(models.Model):
    class Status(models.TextChoices):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="schedules")
    task = models.ForeignKey(PredefinedTask, on_delete=models.PROTECT, related_name="schedules")
    cron_expression = models.CharField(max_length=64)
    inputs = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ENABLED)
    beat_periodic_task_id = models.IntegerField(null=True, blank=True, db_index=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["owner", "status"])]
        ordering = ["-created_at"]

class Execution(models.Model):
    class ExecStatus(models.TextChoices):
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
        STARTED = "STARTED"
        RETRY = "RETRY"

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="executions")
    task_name = models.CharField(max_length=120)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ExecStatus.choices, default=ExecStatus.STARTED)
    runtime_ms = models.IntegerField(null=True, blank=True)
    logs = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["schedule", "-started_at"])]
        ordering = ["-started_at"]
