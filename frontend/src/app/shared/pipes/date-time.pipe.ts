import { Pipe, PipeTransform, inject } from '@angular/core';
import { DateFormatterService } from '@app/core/services/date-formatter.service';

/**
 * Pipe pour formater les dates ISO en format lisible avec heure
 * Usage: {{ created_at | dateTime }}
 */
@Pipe({
  name: 'dateTime',
  standalone: true
})
export class DateTimePipe implements PipeTransform {
  private formatter = inject(DateFormatterService);

  transform(iso: string | undefined): string {
    return this.formatter.formatDateTime(iso);
  }
}
