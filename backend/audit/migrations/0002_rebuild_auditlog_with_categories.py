# Generated manually for audit log enhancement

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('audit', '0001_initial'),
    ]

    operations = [
        # Step 1: Delete all existing audit logs (user confirmed not needed)
        migrations.RunSQL(
            sql="DELETE FROM audit_auditlog;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 2: Drop old table completely
        migrations.DeleteModel(
            name='AuditLog',
        ),

        # Step 3: Create new enhanced AuditLog model
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(
                    choices=[
                        ('HTTP', 'HTTP Request'),
                        ('AUTH', 'Authentication'),
                        ('EVENT', 'Event Management'),
                        ('BOOKING', 'Booking Management'),
                        ('PAYMENT', 'Payment Processing'),
                        ('PARTNER', 'Partner Management'),
                        ('USER', 'User Management'),
                        ('ADMIN', 'Admin Action'),
                        ('SYSTEM', 'System Event'),
                    ],
                    db_index=True,
                    default='HTTP',
                    help_text='Event category for filtering',
                    max_length=20
                )),
                ('level', models.CharField(
                    choices=[
                        ('DEBUG', 'Debug'),
                        ('INFO', 'Info'),
                        ('WARNING', 'Warning'),
                        ('ERROR', 'Error'),
                        ('CRITICAL', 'Critical'),
                    ],
                    db_index=True,
                    default='INFO',
                    help_text='Log severity level',
                    max_length=10
                )),
                ('action', models.CharField(
                    help_text="Action performed (e.g., 'user_login', 'event_created', 'booking_cancelled')",
                    max_length=100
                )),
                ('message', models.TextField(
                    blank=True,
                    help_text='Human-readable description of the event'
                )),
                ('method', models.CharField(
                    blank=True,
                    help_text='HTTP method (GET, POST, PUT, DELETE, etc.)',
                    max_length=8
                )),
                ('path', models.CharField(
                    blank=True,
                    db_index=True,
                    help_text='Request path',
                    max_length=255
                )),
                ('status_code', models.PositiveSmallIntegerField(
                    blank=True,
                    help_text='HTTP status code',
                    null=True
                )),
                ('ip', models.GenericIPAddressField(
                    blank=True,
                    help_text='Client IP address',
                    null=True
                )),
                ('user_agent', models.CharField(
                    blank=True,
                    help_text='User agent string',
                    max_length=255
                )),
                ('duration_ms', models.PositiveIntegerField(
                    default=0,
                    help_text='Request duration in milliseconds'
                )),
                ('resource_type', models.CharField(
                    blank=True,
                    help_text="Type of resource affected (e.g., 'Event', 'Booking', 'Payment')",
                    max_length=50
                )),
                ('resource_id', models.PositiveIntegerField(
                    blank=True,
                    help_text='ID of the affected resource',
                    null=True
                )),
                ('metadata', models.JSONField(
                    blank=True,
                    help_text='Additional context data (before/after values, error details, etc.)',
                    null=True
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    db_index=True,
                    help_text='When this log entry was created'
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    help_text='User who performed the action (null for anonymous or system actions)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'ordering': ['-created_at'],
            },
        ),

        # Step 4: Create optimized indexes
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-created_at'], name='audit_audit_created_cd2419_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['category', '-created_at'], name='audit_audit_categor_f2fc31_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['level', '-created_at'], name='audit_audit_level_6f23d7_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', '-created_at'], name='audit_audit_user_id_9c6c44_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action'], name='audit_audit_action_7b4a85_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['resource_type', 'resource_id'], name='audit_audit_resourc_e3d912_idx'),
        ),
    ]
