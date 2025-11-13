# Simplification du Système de Recommandation d'Événements

## 📋 Résumé des Changements

Le système de recommandation d'événements a été simplifié pour se concentrer sur les correspondances linguistiques et limiter les recommandations à un maximum de 5 événements.

---

## 🎯 Nouveau Système de Scoring

### Scoring Principal (basé sur les langues)

| Priorité | Score | Critère | Description |
|----------|-------|---------|-------------|
| **+++** | 300 pts | Bidirectionnel | L'utilisateur parle la langue de l'événement **ET** apprend cette langue (échange mutuel possible) |
| **++** | 200 pts | Participation active | L'utilisateur parle la langue de l'événement (peut participer activement) |
| **+** | 100 pts | Aide/Support | L'utilisateur peut apporter une aide à l'événement (parle la langue de l'événement + autres langues) |

### Bonus de Tri (ne changent pas le statut "recommandé")

| Bonus | Score | Critère |
|-------|-------|---------|
| Proximité | +40 pts | Événement dans la ville de l'utilisateur |
| Gratuit | +20 pts | Prix = 0€ |
| Bientôt | +10 pts | Événement dans les 7 prochains jours |
| Presque complet | +5 pts | Taux d'occupation ≥ 80% |

### Pénalités (logique conservée)

| Pénalité | Score | Critère |
|----------|-------|---------|
| Déjà réservé | -300 pts | L'utilisateur a déjà réservé |
| Complet | -1200 pts | Plus de places disponibles |
| Annulé | -1300 pts | Événement annulé |
| Passé | -1500 pts | Événement terminé |

---

## 🏷️ Système de Badges Simplifié

### Avant (6 types de badges)
```typescript
export type PriorityBadge =
  | 'bidirectional'
  | 'target_language'
  | 'support'
  | 'almost_full'
  | 'full'
  | 'cancelled';
```

### Après (3 types de badges)
```typescript
export type PriorityBadge =
  | 'recommended'  // ✨ Nouveau badge unique pour toutes les recommandations
  | 'full'         // ⚠️ Événement complet
  | 'cancelled';   // ❌ Événement annulé
```

### Affichage des Badges

- **Recommandé** (accent) : Événements avec score ≥ 100 pts (top 5 maximum)
- **Complet** (danger) : Événement sans places disponibles
- **Annulé** (danger) : Événement annulé

---

## 🔢 Limitation des Recommandations

### Règle des 5 Recommandations Maximum

Le système limite automatiquement le nombre d'événements marqués comme "recommandés" à **5 maximum**.

**Logique d'implémentation** :
1. Tous les événements sont scorés selon les critères linguistiques
2. Les événements sont triés par score décroissant
3. Seuls les **5 premiers** événements avec un score ≥ 100 reçoivent le badge "Recommandé"
4. Les autres événements restent visibles mais sans badge de recommandation

**Code** (`sortEvents` method) :
```typescript
sortEvents(events: EventDto[], criteria: SortingCriteria): ScoredEvent[] {
  const scored = events.map(event => this.scoreEvent(event, criteria));
  const sorted = scored.sort((a, b) => b.score - a.score);

  // Limiter les recommandations à 5 événements maximum
  let recommendedCount = 0;
  const maxRecommendations = 5;

  return sorted.map(scoredEvent => {
    if (scoredEvent.isRecommended &&
        scoredEvent.badgeReason === 'recommended' &&
        recommendedCount >= maxRecommendations) {
      return {
        ...scoredEvent,
        isRecommended: false,
        badgeReason: null
      };
    }

    if (scoredEvent.isRecommended && scoredEvent.badgeReason === 'recommended') {
      recommendedCount++;
    }

    return scoredEvent;
  });
}
```

---

## 📁 Fichiers Modifiés

### 1. `events-sorting.service.ts`
**Localisation** : `frontend/src/app/features/events/services/events-sorting.service.ts`

**Modifications** :
- ✅ Simplifié `PriorityBadge` type (ligne 19-22)
- ✅ Ajouté limite de 5 recommandations dans `sortEvents()` (lignes 37-65)
- ✅ Réécrit `scoreEvent()` avec nouveau système de scoring (lignes 67-153)
- ✅ Ajouté documentation détaillée du nouveau système

### 2. `event-card.component.ts`
**Localisation** : `frontend/src/app/features/events/components/event-card/event-card.component.ts`

**Modifications** :
- ✅ Simplifié `priorityBadgeLabel` getter (lignes 108-119)
- ✅ Simplifié `priorityBadgeVariant` getter (lignes 121-131)
- ✅ Supprimé les références aux anciens badges

### 3. Fichiers de Traduction

#### `fr.json`
**Localisation** : `frontend/src/assets/i18n/fr.json`

**Avant** :
```json
"badges": {
    "match_bidirectional": "Langues compatibles",
    "target_language": "Ma langue cible",
    "support": "Je peux aider",
    "almost_full": "Quasi complet",
    "full": "Complet",
    "cancelled": "Annulé"
}
```

**Après** :
```json
"badges": {
    "recommended": "Recommandé",
    "full": "Complet",
    "cancelled": "Annulé"
}
```

#### `en.json`
**Localisation** : `frontend/src/assets/i18n/en.json`

**Avant** :
```json
"badges": {
    "match_bidirectional": "Language match",
    "target_language": "My target language",
    "support": "I can help",
    "almost_full": "Almost full",
    "full": "Full",
    "cancelled": "Cancelled"
}
```

**Après** :
```json
"badges": {
    "recommended": "Recommended",
    "full": "Full",
    "cancelled": "Cancelled"
}
```

#### `nl.json`
**Note** : Le fichier `nl.json` ne contenait pas de section `events.badges` auparavant. Aucune modification nécessaire pour l'instant.

---

## ✅ Tests et Validation

### Build Frontend
```bash
cd frontend && npm run build
```

**Résultat** : ✅ **SUCCESS**
- Aucune erreur TypeScript
- Build complété en 8.588 secondes
- Warning : Bundle initial légèrement au-dessus du budget (522 KB vs 500 KB) - non critique

### Vérifications Effectuées

1. ✅ **Compilation TypeScript** : Aucune erreur
2. ✅ **Types de badges** : Correctement simplifiés
3. ✅ **Références dans les templates** : Aucune référence aux anciens badges
4. ✅ **Traductions** : Mises à jour pour FR et EN
5. ✅ **Logique de limitation** : Maximum 5 recommandations implémenté

---

## 🎨 Comportement Utilisateur

### Scénario 1 : Utilisateur avec correspondances linguistiques

**Profil** :
- Langues natives : Français, Anglais
- Langues cibles : Espagnol, Néerlandais

**Événements disponibles** :
- 10 événements en Espagnol
- 5 événements en Français
- 3 événements en Néerlandais
- 8 événements en Allemand

**Résultat** :
1. Les **5 meilleurs événements** (combinaison de score linguistique + proximité + gratuité) reçoivent le badge "Recommandé"
2. Les autres événements restent visibles mais sans badge
3. Ordre de priorité :
   - Événements en Espagnol (utilisateur apprend) : score 200-300 pts
   - Événements en Français (utilisateur parle) : score 200 pts
   - Événements en Néerlandais (utilisateur apprend) : score 200-300 pts
   - Événements en Allemand (aucune correspondance) : pas recommandé

### Scénario 2 : Utilisateur débutant (peu de correspondances)

**Profil** :
- Langues natives : Français
- Langues cibles : Anglais

**Événements disponibles** :
- 3 événements en Anglais
- 2 événements en Français
- 10 événements dans d'autres langues

**Résultat** :
1. Maximum **5 événements** recommandés parmi ceux en Anglais ou Français
2. Les autres événements visibles mais non recommandés
3. Filtrage naturel basé sur les langues pertinentes

---

## 📊 Impact sur les Performances

### Avant
- Calculs complexes avec 6 types de badges
- Tous les événements pouvaient être "recommandés" selon différents critères
- Logique de tri dispersée

### Après
- Logique simplifiée avec 3 types de badges
- Maximum 5 recommandations claires et ciblées
- Performances maintenues (aucun impact négatif)
- Code plus lisible et maintenable

---

## 🚀 Prochaines Étapes Possibles

### Améliorations Futures (optionnelles)

1. **Personnalisation du nombre de recommandations**
   - Permettre à l'utilisateur de choisir combien de recommandations afficher (3, 5, 10)

2. **Machine Learning**
   - Analyser les événements auxquels l'utilisateur participe
   - Affiner les recommandations basées sur l'historique

3. **Feedback utilisateur**
   - Ajouter un bouton "Cette recommandation est pertinente / non pertinente"
   - Améliorer l'algorithme selon les retours

4. **Notifications**
   - Alerter l'utilisateur quand un nouvel événement recommandé est publié

5. **Traduction NL**
   - Ajouter la section `events.badges` dans `nl.json` si nécessaire

---

## 📚 Références

### Fichiers Clés
- **Service** : `frontend/src/app/features/events/services/events-sorting.service.ts`
- **Composant** : `frontend/src/app/features/events/components/event-card/event-card.component.ts`
- **Traductions** : `frontend/src/assets/i18n/*.json`

### Documentation Liée
- `SECURITY_SQL_INJECTION.md` - Sécurité de l'application
- `POSTMAN_TESTS_CORRECTED.md` - Tests API
- `GAMES_SYSTEM_DOCUMENTATION.md` - Système de jeux

---

**Document créé le** : 2025-01-13
**Dernière révision** : 2025-01-13
**Auteur** : Système de recommandation simplifié
