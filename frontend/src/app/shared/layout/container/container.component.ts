import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'shared-container',
  standalone: true,
  templateUrl: './container.component.html',
  styleUrls: ['./container.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContainerComponent {}
