# ADR 003: Stripe TEST Mode Uniquement

**Date**: 2024-12-20
**Statut**: ✅ Accepté
**Décideurs**: Équipe Backend, Product Owner

## Contexte

L'application Conversa nécessite une intégration Stripe pour gérer les paiements d'événements. La question se pose : utiliser **sk_test_** (mode TEST) ou **sk_live_** (mode LIVE) ?

## Décision

**Forcer le mode TEST Stripe (`sk_test_*`) en développement ET production.**

### Implémentation

```python
# payments/constants.py
REQUIRE_TEST_MODE = True  # Force sk_test_ keys only

# payments/validators.py
def validate_stripe_test_mode():
    if not REQUIRE_TEST_MODE:
        return

    key = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        raise ValidationError(
            "Stripe TEST mode required. "
            "STRIPE_SECRET_KEY must start with 'sk_test_'."
        )

# config/settings/base.py (ligne 129-132)
if STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith('sk_test_'):
    raise ImproperlyConfigured(
        "STRIPE_SECRET_KEY must start with 'sk_test_' (TEST mode only)."
    )
```

### Validation

- ✅ **Au démarrage Django** : Check dans settings
- ✅ **À chaque paiement** : Validation dans `PaymentService.create_checkout_session()`
- ✅ **Tests** : Vérifient enforcement sk_test_

## Justification

### Pourquoi mode TEST uniquement ?

1. **Pas d'argent réel** : Transactions fictives (cartes test Stripe)
2. **Sécurité** : Aucun risque de prélèvement réel
3. **Développement** : Permet tests complets sans coût
4. **Démo** : Présentation produit sans paiements réels
5. **Évolutivité** : Migration vers sk_live_ facile si besoin futur

### Cartes de test Stripe

```
Succès : 4242 4242 4242 4242
Échec  : 4000 0000 0000 0002
3D Secure : 4000 0025 0000 3155
```

## Configuration

### Développement

```env
# .env.dev
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### Production

```env
# .env.prod
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # TEST mode aussi en prod !
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

## Avantages

✅ **Pas de paiements réels** : Zéro risque financier
✅ **Tests illimités** : Pas de frais Stripe
✅ **Démo safe** : Présentation produit sans danger
✅ **Développement facile** : Pas besoin compte bancaire réel
✅ **Validation stricte** : Impossible d'utiliser sk_live_ par erreur

## Inconvénients

⚠️ **Pas de revenus réels** : Application ne génère pas d'argent
⚠️ **Migration nécessaire** : Si passage au réel, changer clés + retirer validation

## Migration vers mode LIVE (si nécessaire)

Si un jour décision de passer en mode LIVE :

1. Modifier `payments/constants.py` : `REQUIRE_TEST_MODE = False`
2. Retirer check dans `config/settings/base.py` ligne 129-132
3. Mettre à jour clés :
   ```env
   STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
   STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
   ```
4. Re-tester tous les flows de paiement
5. Configurer webhooks production Stripe

## Décisions liées

- **ADR 001**: PaymentService valide TEST mode
- Logs audit : Tous paiements loggés (test ou live)

## Références

- [Stripe Testing Documentation](https://stripe.com/docs/testing)
- [Stripe Test Cards](https://stripe.com/docs/testing#cards)
