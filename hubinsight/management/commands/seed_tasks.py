from django.core.management.base import BaseCommand
from hubinsight.models import PredefinedTask
from hubinsight.task_registry import REGISTRY

class Command(BaseCommand):
    help = "Seed predefined tasks from registry"

    def handle(self, *args, **kwargs):
        created = 0
        for name, meta in REGISTRY.items():
            _, was_created = PredefinedTask.objects.update_or_create(
                name=name,
                defaults=dict(
                    description=meta.get("description", ""),
                    inputs_schema=meta.get("inputs_schema", []),
                    is_schedulable=meta.get("schedulable", True),
                )
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded. New: {created}"))
