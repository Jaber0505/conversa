// frontend/src/app/features/shared/site-header/site-header.component.ts
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TPipe } from '@app/core/i18n/t.pipe';
import { TAttrDirective } from '@app/core/i18n/t-attr.directive';
import { LangService } from '@app/core/i18n/lang.service';
import { I18nService } from '@app/core/i18n/i18n.service';
import { LangModalComponent, Lang } from '../lang-modal/lang-modal.component';

@Component({
    selector: 'app-site-header',
    standalone: true,
    imports: [CommonModule, RouterLink, TPipe, TAttrDirective, LangModalComponent],
    templateUrl: './site-header.component.html',
    styleUrls: ['./site-header.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush
})
export class SiteHeaderComponent {
    private readonly langSvc = inject(LangService);
    private readonly i18n = inject(I18nService);

    readonly langs: Lang[] = ['fr', 'en', 'nl'];
    readonly current = signal<Lang>(this.langSvc.current as Lang);
    readonly showLangModal = signal(false);

    labelFor(l: Lang) {
        return this.i18n.t(`home.search.lang.${l}`);
    }

    openLangModal() {
        this.showLangModal.set(true);
    }

    closeLangModal() {
        this.showLangModal.set(false);
    }

    applyLang(l: Lang) {
        if (l === this.current()) {
            this.closeLangModal();
            return;
        }
        this.langSvc.set(l);
        this.current.set(l);
        this.closeLangModal();
    }

    onLangSaved(l: Lang) {
        this.langSvc.set(l);
        this.current.set(l);
        this.closeLangModal();
    }
}
