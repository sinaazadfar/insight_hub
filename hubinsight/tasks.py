import time
from celery import shared_task
from django.utils import timezone
from .models import Execution, Schedule

@shared_task
def my_ping():
    return "pong"

def _start_execution(schedule_id, task_name):
    return Execution.objects.create(schedule_id=schedule_id, task_name=task_name)


def _finish_execution(ex, status, logs=None, started=None):
    ex.status = status
    ex.finished_at = timezone.now()
    if started:
        delta = (ex.finished_at - started).total_seconds() * 1000
        ex.runtime_ms = int(delta)
    if logs is not None:
        ex.logs = logs
    ex.save()

@shared_task(bind=True)
def run_predefined_task(self, schedule_id, task_name, inputs):
    started = timezone.now()
    ex = _start_execution(schedule_id, task_name)
    try:
        time.sleep(0.2)
        result = {"echo": inputs, "ts": started.isoformat()}
        _finish_execution(ex, "SUCCESS", logs=result, started=started)
    except Exception as e:
        _finish_execution(ex, "FAILURE", logs={"error": str(e)}, started=started)
        raise
    Schedule.objects.filter(pk=schedule_id).update(last_run_at=started)
