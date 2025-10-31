"""
Management command to export audit logs to CSV.

Supports filtering by date range, category, level, and user.
Exports comprehensive audit data including metadata for business events.

Usage:
    python manage.py export_audit
    python manage.py export_audit --from 2025-01-01 --to 2025-12-31
    python manage.py export_audit --category AUTH --level ERROR
    python manage.py export_audit --out /path/to/export.csv
"""
import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from audit.models import AuditLog


def _parse_dt(val, end=False):
    """
    Parse datetime string in ISO 8601 format.

    Args:
        val: Date/datetime string (e.g., '2025-08-01' or '2025-08-01T10:00:00Z')
        end: If True, use end of day for date-only strings

    Returns:
        Timezone-aware datetime or None

    Raises:
        CommandError: If format is invalid
    """
    if not val:
        return None

    dt = parse_datetime(val)
    if dt is None:
        d = parse_date(val)
        if d is None:
            raise CommandError(
                f"Invalid date/datetime format: '{val}'. Expected ISO 8601 format "
                "(e.g., '2025-08-01' or '2025-08-01T10:00:00Z')"
            )
        t = timezone.datetime.max.time() if end else timezone.datetime.min.time()
        dt = timezone.make_aware(
            timezone.datetime.combine(d, t),
            timezone.get_current_timezone()
        )

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())

    return dt


class Command(BaseCommand):
    help = "Export audit logs to CSV file"

    def add_arguments(self, parser):
        # Date filtering
        parser.add_argument(
            "--from",
            dest="date_from",
            help="Start date/datetime in ISO format (e.g., 2025-08-01 or 2025-08-01T10:00:00Z)"
        )
        parser.add_argument(
            "--to",
            dest="date_to",
            help="End date/datetime in ISO format"
        )

        # Category and level filtering
        parser.add_argument(
            "--category",
            dest="category",
            choices=[c[0] for c in AuditLog.Category.choices],
            help="Filter by category (HTTP, AUTH, EVENT, BOOKING, PAYMENT, etc.)"
        )
        parser.add_argument(
            "--level",
            dest="level",
            choices=[l[0] for l in AuditLog.Level.choices],
            help="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
        )

        # User filtering
        parser.add_argument(
            "--user",
            dest="user_id",
            type=int,
            help="Filter by user ID"
        )

        # Path filtering (for HTTP logs)
        parser.add_argument(
            "--only-api-v1",
            action="store_true",
            help="Limit to /api/v1/ paths only"
        )

        # Output options
        parser.add_argument(
            "--out",
            dest="out",
            default="audit/exports/audit_export.csv",
            help="Output file path (relative to /app directory)"
        )
        parser.add_argument(
            "--include-metadata",
            action="store_true",
            help="Include metadata column (JSON)"
        )

    def handle(self, *args, **opts):
        # Build queryset with filters
        qs = AuditLog.objects.all().select_related("user")

        # Date range filtering
        d_from = _parse_dt(opts.get("date_from"), end=False)
        d_to = _parse_dt(opts.get("date_to"), end=True)
        if d_from:
            qs = qs.filter(created_at__gte=d_from)
            self.stdout.write(f"  Filtering from: {d_from.strftime('%Y-%m-%d %H:%M:%S')}")
        if d_to:
            qs = qs.filter(created_at__lte=d_to)
            self.stdout.write(f"  Filtering to: {d_to.strftime('%Y-%m-%d %H:%M:%S')}")

        # Category filtering
        if opts.get("category"):
            qs = qs.filter(category=opts["category"])
            self.stdout.write(f"  Filtering category: {opts['category']}")

        # Level filtering
        if opts.get("level"):
            qs = qs.filter(level=opts["level"])
            self.stdout.write(f"  Filtering level: {opts['level']}")

        # User filtering
        if opts.get("user_id"):
            qs = qs.filter(user_id=opts["user_id"])
            self.stdout.write(f"  Filtering user ID: {opts['user_id']}")

        # Path filtering
        if opts.get("only_api_v1"):
            qs = qs.filter(path__startswith="/api/v1/")
            self.stdout.write("  Filtering paths: /api/v1/* only")

        # Order by creation date
        qs = qs.order_by("created_at")

        # Ensure output directory exists
        out_path = Path(opts["out"])
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Define CSV fields
        fields = [
            "created_at",
            "category",
            "level",
            "action",
            "message",
            "user_email",
            "user_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "ip",
            "user_agent",
            "resource_type",
            "resource_id",
        ]

        if opts.get("include_metadata"):
            fields.append("metadata")

        # Write CSV
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)

            for log in qs:
                row = [
                    timezone.localtime(log.created_at).isoformat(),
                    log.category,
                    log.level,
                    log.action,
                    log.message,
                    log.user.email if log.user else "",
                    log.user.id if log.user else "",
                    log.method or "",
                    log.path or "",
                    log.status_code or "",
                    log.duration_ms,
                    log.ip or "",
                    log.user_agent or "",
                    log.resource_type or "",
                    log.resource_id or "",
                ]

                if opts.get("include_metadata"):
                    metadata_str = json.dumps(log.metadata) if log.metadata else ""
                    row.append(metadata_str)

                writer.writerow(row)

        # Success message
        count = qs.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Export completed: {count:,} logs exported to {out_path.resolve()}"
            )
        )
