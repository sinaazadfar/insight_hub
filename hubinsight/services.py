from datetime import datetime
from croniter import croniter
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django.utils import timezone
import json
from .models import Schedule

def validate_cron_5_detailed(cron: str):
    if not isinstance(cron, str) or cron.strip() == "":
        return False, "Cron expression is required."
    parts = cron.split()
    if len(parts) != 5:
        return False, "Cron must have exactly 5 fields: minute hour day month dow"
    try:
        croniter(cron, timezone.now())
        return True, None
    except Exception as e:
        return False, f"Invalid cron: {e}"


def compute_next_run_at(cron: str):
    base = timezone.now()
    itr = croniter(cron, base)
    next_dt = itr.get_next(datetime)
    if timezone.is_naive(next_dt):
        next_dt = timezone.make_aware(next_dt, timezone.get_current_timezone())
    return next_dt


def ensure_periodic_task(schedule: Schedule):
    m, h, dom, mon, dow = schedule.cron_expression.split()
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=m,
        hour=h,
        day_of_month=dom,
        month_of_year=mon,
        day_of_week=dow,
        timezone=str(timezone.get_current_timezone()),
    )

    args = [schedule.id, schedule.task.name, schedule.inputs]
    name = f"schedule:{schedule.id}:{schedule.task.name}"
    defaults = dict(
        crontab=crontab,
        task="hubinsight.tasks.run_predefined_task",
        args=json.dumps(args),
        enabled=(schedule.status == Schedule.Status.ENABLED),
    )

    if schedule.beat_periodic_task_id:
        PeriodicTask.objects.filter(id=schedule.beat_periodic_task_id).update(**defaults, name=name)
    else:
        pt = PeriodicTask.objects.create(name=name, **defaults)
        schedule.beat_periodic_task_id = pt.id

    try:
        schedule.next_run_at = compute_next_run_at(schedule.cron_expression)
    except Exception:
        schedule.next_run_at = None

    schedule.save(update_fields=["beat_periodic_task_id", "next_run_at"])
