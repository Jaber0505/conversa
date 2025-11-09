import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { AuditApiService } from '@core/http';
import type { AuditLog } from '@core/http';
import { SHARED_IMPORTS } from '@shared';

@Component({
  standalone: true,
  selector: 'app-audit-logs',
  templateUrl: './audit-logs.component.html',
  styleUrls: ['./audit-logs.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ReactiveFormsModule, ...SHARED_IMPORTS],
})
export class AuditLogsComponent {
  private readonly api = inject(AuditApiService);
  private readonly fb = inject(FormBuilder);

  loading = signal(false);
  error = signal<string | null>(null);
  items = signal<AuditLog[]>([]);
  total = signal(0);
  notice = signal<string | null>(null);

  // Stats
  stats = signal<{ category: string; level: string; count: number }[]>([]);
  catTotals = signal<{ key: string; count: number }[]>([]);
  levelTotals = signal<{ key: string; count: number }[]>([]);

  form = this.fb.group({
    search: [''],
    category: [''],
    level: [''],
    method: [''],
    status_code: [''],
    created_at__gte: [''],
    created_at__lte: [''],
  });

  ngOnInit() { this.fetch(); this.loadStats(); }

  fetch(page = 1) {
    this.loading.set(true);
    this.error.set(null);
    const params: any = { page, page_size: 25, ...this.form.getRawValue() };
    this.api.list(params).subscribe({
      next: (res) => { this.items.set(res.results); this.total.set(res.count); this.loading.set(false); },
      error: () => { this.error.set('Erreur de chargement des logs'); this.loading.set(false); }
    });
  }

  exportCsv() {
    const params: any = { ...this.form.getRawValue() };
    this.api.exportCsv(params).subscribe(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'audit_logs.csv'; a.click(); URL.revokeObjectURL(url);
    });
  }

  loadStats() {
    this.api.stats().subscribe({
      next: (res: any[]) => {
        this.stats.set(res as any);
        // Aggregate by category
        const byCat = new Map<string, number>();
        const byLevel = new Map<string, number>();
        for (const it of res as any[]) {
          byCat.set(it.category, (byCat.get(it.category) || 0) + Number(it.count || 0));
          byLevel.set(it.level, (byLevel.get(it.level) || 0) + Number(it.count || 0));
        }
        this.catTotals.set(Array.from(byCat.entries()).map(([key, count]) => ({ key, count })).sort((a,b)=>b.count-a.count));
        this.levelTotals.set(Array.from(byLevel.entries()).map(([key, count]) => ({ key, count })).sort((a,b)=>b.count-a.count));
      },
      error: () => { /* ignore */ },
    });
  }

  cleanup() {
    if (!confirm('Confirmer le nettoyage des anciens logs (selon politique de rétention) ?')) return;
    this.loading.set(true);
    this.notice.set(null);
    this.api.cleanup().subscribe({
      next: (res) => {
        this.notice.set(res?.message || 'Nettoyage terminé');
        this.loading.set(false);
        this.fetch();
        this.loadStats();
      },
      error: (e) => {
        this.error.set('Echec du nettoyage');
        this.loading.set(false);
      }
    });
  }

  cleanupAll() {
    const confirmed = confirm(
      '⚠️ ATTENTION : Supprimer TOUS les logs d\'audit ?\n\n' +
      'Cette action est IRRÉVERSIBLE et supprimera tous les logs sans exception.\n\n' +
      'Cliquez sur OK pour continuer ou Annuler pour annuler.'
    );
    if (!confirmed) return;

    // Double confirmation
    const doubleConfirm = confirm(
      '⚠️ DERNIÈRE CONFIRMATION ⚠️\n\n' +
      'Vous êtes sur le point de SUPPRIMER TOUS LES LOGS.\n\n' +
      'Êtes-vous absolument sûr ?'
    );
    if (!doubleConfirm) return;

    this.loading.set(true);
    this.notice.set(null);
    this.api.purgeAll().subscribe({
      next: (res) => {
        this.notice.set(`✅ ${res?.deleted || 0} logs supprimés (reset complet)`);
        this.loading.set(false);
        this.fetch();
        this.loadStats();
      },
      error: (e) => {
        this.error.set('Echec de la suppression');
        this.loading.set(false);
      }
    });
  }

  // Helpers for template (avoid optional chaining warnings)
  maxCat(): number {
    const arr = this.catTotals();
    return Math.max(1, (arr[0]?.count ?? 1));
  }
  maxLevel(): number {
    const arr = this.levelTotals();
    return Math.max(1, (arr[0]?.count ?? 1));
  }
}
