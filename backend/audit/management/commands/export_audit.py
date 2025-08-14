# backend/audit/management/commands/export_audit.py
import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from audit.models import AuditLog

def _parse_dt(val, end=False):
    if not val:
        return None
    dt = parse_datetime(val)
    if dt is None:
        d = parse_date(val)
        if d is None:
            raise CommandError("Format date/datetime invalide (attendu ISO 8601).")
        t = timezone.datetime.max.time() if end else timezone.datetime.min.time()
        dt = timezone.make_aware(timezone.datetime.combine(d, t), timezone.get_current_timezone())
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

class Command(BaseCommand):
    help = "Exporte les logs d’audit en CSV."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="date_from", help="Date/Datetime ISO (ex: 2025-08-01 ou 2025-08-01T10:00:00Z)")
        parser.add_argument("--to", dest="date_to", help="Date/Datetime ISO")
        parser.add_argument("--out", dest="out", default="audit/exports/audit_export.csv", help="Chemin de sortie (relatif au dossier /app)")
        parser.add_argument("--only-api-v1", action="store_true", help="Limiter aux chemins /api/v1/...")

    def handle(self, *args, **opts):
        qs = AuditLog.objects.all().select_related("user")
        d_from = _parse_dt(opts.get("date_from"), end=False)
        d_to = _parse_dt(opts.get("date_to"), end=True)
        if d_from: qs = qs.filter(created_at__gte=d_from)
        if d_to:   qs = qs.filter(created_at__lte=d_to)
        if opts.get("only_api_v1"): qs = qs.filter(path__startswith="/api/v1/")

        out_path = Path(opts["out"])
        out_path.parent.mkdir(parents=True, exist_ok=True)

        fields = ["created_at","user","method","path","status_code","duration_ms","ip","user_agent"]
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(fields)
            for r in qs.order_by("created_at"):
                w.writerow([
                    timezone.localtime(r.created_at).isoformat(),
                    r.user.username if r.user_id else "",
                    r.method, r.path, r.status_code, r.duration_ms,
                    r.ip or "", r.user_agent or ""
                ])
        self.stdout.write(self.style.SUCCESS(f"Export: {qs.count()} lignes -> {out_path.resolve()}"))
