"""
Management command to clean up old audit logs.

Implements retention policies based on audit log category and level:
- HTTP logs: 90 days
- Auth logs: 1 year
- Business logs (payment, booking): 7 years
- Error logs: 1 year
- Other logs: 6 months (default)

Usage:
    python manage.py cleanup_old_audits
    python manage.py cleanup_old_audits --dry-run
    python manage.py cleanup_old_audits --verbose
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from audit.models import AuditLog
from common.constants import (
    AUDIT_RETENTION_HTTP,
    AUDIT_RETENTION_AUTH,
    AUDIT_RETENTION_BUSINESS,
    AUDIT_RETENTION_ERROR,
    AUDIT_RETENTION_DEFAULT,
)


class Command(BaseCommand):
    help = "Clean up old audit logs based on retention policies"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed statistics for each category",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        now = timezone.now()

        # Define retention policies
        retention_policies = [
            {
                "name": "HTTP Requests",
                "days": AUDIT_RETENTION_HTTP,
                "query": Q(category=AuditLog.Category.HTTP),
            },
            {
                "name": "Authentication",
                "days": AUDIT_RETENTION_AUTH,
                "query": Q(category=AuditLog.Category.AUTH),
            },
            {
                "name": "Business Events (Payment/Booking)",
                "days": AUDIT_RETENTION_BUSINESS,
                "query": Q(category__in=[
                    AuditLog.Category.PAYMENT,
                    AuditLog.Category.BOOKING,
                ]),
            },
            {
                "name": "Errors",
                "days": AUDIT_RETENTION_ERROR,
                "query": Q(level__in=[
                    AuditLog.Level.ERROR,
                    AuditLog.Level.CRITICAL,
                ]),
            },
            {
                "name": "Other Categories",
                "days": AUDIT_RETENTION_DEFAULT,
                "query": Q(category__in=[
                    AuditLog.Category.EVENT,
                    AuditLog.Category.PARTNER,
                    AuditLog.Category.USER,
                    AuditLog.Category.ADMIN,
                    AuditLog.Category.SYSTEM,
                ]),
            },
        ]

        total_deleted = 0
        total_kept = 0

        self.stdout.write(
            self.style.WARNING("🧹 Audit Log Cleanup") if not dry_run
            else self.style.NOTICE("🔍 Audit Log Cleanup (DRY RUN)")
        )
        self.stdout.write("")

        for policy in retention_policies:
            cutoff_date = now - timedelta(days=policy["days"])
            queryset = AuditLog.objects.filter(
                policy["query"],
                created_at__lt=cutoff_date
            )

            count_to_delete = queryset.count()
            count_kept = AuditLog.objects.filter(
                policy["query"],
                created_at__gte=cutoff_date
            ).count()

            if verbose or count_to_delete > 0:
                self.stdout.write(
                    f"  📂 {policy['name']}: "
                    f"Retention {policy['days']} days"
                )
                self.stdout.write(
                    f"     Cutoff: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.stdout.write(
                    f"     To delete: {count_to_delete:,} | "
                    f"To keep: {count_kept:,}"
                )

            if not dry_run and count_to_delete > 0:
                deleted_count, _ = queryset.delete()
                total_deleted += deleted_count
                self.stdout.write(
                    self.style.SUCCESS(f"     ✓ Deleted {deleted_count:,} logs")
                )
            else:
                total_deleted += count_to_delete

            total_kept += count_kept
            self.stdout.write("")

        # Summary
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(
            f"  📊 SUMMARY: "
            f"{total_deleted:,} logs {'would be ' if dry_run else ''}deleted, "
            f"{total_kept:,} logs kept"
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    "\n  ℹ️  This was a dry run. No logs were actually deleted."
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    "  Run without --dry-run to perform the cleanup."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  ✅ Cleanup completed successfully!"
                )
            )

        # Show oldest and newest logs
        if verbose:
            oldest_log = AuditLog.objects.order_by("created_at").first()
            newest_log = AuditLog.objects.order_by("-created_at").first()

            if oldest_log:
                self.stdout.write("")
                self.stdout.write(
                    f"  Oldest log: {oldest_log.created_at.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"[{oldest_log.category}]"
                )
            if newest_log:
                self.stdout.write(
                    f"  Newest log: {newest_log.created_at.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"[{newest_log.category}]"
                )
