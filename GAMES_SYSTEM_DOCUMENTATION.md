# Documentation du Système de Jeux Collaboratifs - Conversa

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Modèles de données](#modèles-de-données)
4. [Types de jeux disponibles](#types-de-jeux-disponibles)
5. [Flux de fonctionnement](#flux-de-fonctionnement)
6. [API Endpoints](#api-endpoints)
7. [Interface utilisateur](#interface-utilisateur)
8. [Règles métier](#règles-métier)
9. [Gestion du contenu](#gestion-du-contenu)
10. [Système de vote et complétion](#système-de-vote-et-complétion)
11. [Scénarios d'utilisation](#scénarios-dutilisation)

---

## Vue d'ensemble

Le système de jeux collaboratifs de Conversa permet aux organisateurs d'événements de créer des jeux interactifs en temps réel pendant leurs événements de pratique linguistique. Les participants votent collectivement sur des réponses, favorisant l'apprentissage collaboratif et l'engagement.

### Objectifs principaux

- **Apprentissage ludique** : Favoriser l'apprentissage des langues de manière interactive
- **Collaboration** : Encourager le travail d'équipe et la discussion
- **Engagement** : Maintenir l'intérêt des participants pendant l'événement
- **Temps réel** : Fournir des statistiques et résultats instantanés

### Caractéristiques clés

✅ **2 types de jeux** : Description d'image et Association de mots
✅ **3 niveaux de difficulté** : Facile, Moyen, Difficile
✅ **Multilingue** : Support pour FR, EN, NL
✅ **Vote collaboratif** : Les participants votent pour la meilleure réponse
✅ **Complétion automatique** : Détection de la majorité ou vote complet
✅ **Timeout automatique** : Fin du jeu après le temps imparti (1-30 minutes)
✅ **Statistiques en temps réel** : Mise à jour toutes les 3 secondes
✅ **Historique** : Conservation de tous les jeux passés

---

## Architecture du système

### Stack technique

**Backend** : Django REST Framework
- Models : `Game`, `GameVote`
- Service Layer : `GameService` (Single Source of Truth)
- Views : `GameViewSet` (REST API)
- Content : Fichiers JSON pour les questions

**Frontend** : Angular 18 (Standalone Components)
- Components : `GamesComponent`, `GameCreateComponent`, `GamePlayComponent`, `GameResultsComponent`
- Service : `GamesApiService`
- State Management : Signals
- Polling : RxJS intervals pour les mises à jour temps réel

### Principe architectural

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                        │
├─────────────────────────────────────────────────────────────┤
│  GamesComponent (Orchestrateur)                             │
│    ├── GameCreateComponent (Création - Organisateur)        │
│    ├── GamePlayComponent (Jeu actif - Tous)                 │
│    └── GameResultsComponent (Résultats - Tous)              │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Django)                          │
├─────────────────────────────────────────────────────────────┤
│  GameViewSet (API Layer)                                     │
│    └── GameService (Business Logic - SSOT)                  │
│         └── Models: Game, GameVote                          │
│         └── Content: JSON files                             │
└─────────────────────────────────────────────────────────────┘
```

**SSOT (Single Source of Truth)** : `GameService` est le point unique contenant toute la logique métier. Les views ne font que valider les entrées et appeler le service.

---

## Modèles de données

### 1. Modèle `Game`

Table : `games_game`

```python
class Game(models.Model):
    # Identifiants
    id = IntegerField (PK)
    public_id = UUIDField (Unique, Indexed)

    # Relations
    event = ForeignKey(Event, related_name="games")
    created_by = ForeignKey(User, related_name="created_games")

    # Configuration du jeu
    game_type = CharField (picture_description | word_association)
    difficulty = CharField (easy | medium | hard)
    language_code = CharField (fr | en | nl)

    # Contenu du jeu
    question_id = CharField (ID depuis JSON)
    question_text = TextField (Question dénormalisée)
    correct_answer = CharField (Réponse correcte)
    image_url = URLField (Optionnel, pour picture_description)

    # Timeout
    timeout_minutes = PositiveIntegerField (1-30 minutes)
    timeout_at = DateTimeField (Calculé automatiquement)

    # Statut et résultat
    status = CharField (ACTIVE | COMPLETED | TIMEOUT)
    completed_at = DateTimeField (Nullable)
    is_correct = BooleanField (Nullable - True si équipe a réussi)
    final_answer = CharField (Réponse choisie par majorité)

    # Timestamps
    created_at = DateTimeField (auto_now_add)
    updated_at = DateTimeField (auto_now)
```

**Index de base de données** :
```sql
CREATE INDEX idx_event_status ON games_game (event_id, status);
CREATE INDEX idx_status_timeout ON games_game (status, timeout_at);
CREATE INDEX idx_public_id ON games_game (public_id);
CREATE INDEX idx_created_at ON games_game (created_at);
```

**Propriétés calculées** :
```python
@property
def is_expired(self) -> bool:
    """Vérifie si le délai est dépassé"""
    return self.status == 'ACTIVE' and timezone.now() >= self.timeout_at

@property
def time_remaining_seconds(self) -> int:
    """Retourne les secondes restantes (0 si expiré)"""
    if self.status != 'ACTIVE':
        return 0
    remaining = (self.timeout_at - timezone.now()).total_seconds()
    return max(0, int(remaining))
```

**Méthodes de transition d'état** :
```python
def mark_completed(self, is_correct: bool, final_answer: str):
    """Marque le jeu comme terminé avec succès ou échec"""
    self.status = GameStatus.COMPLETED
    self.completed_at = timezone.now()
    self.is_correct = is_correct
    self.final_answer = final_answer
    self.save()

def mark_timeout(self):
    """Marque le jeu comme expiré sans réponse"""
    self.status = GameStatus.TIMEOUT
    self.completed_at = timezone.now()
    self.save()
```

### 2. Modèle `GameVote`

Table : `games_gamevote`

```python
class GameVote(models.Model):
    # Relations
    game = ForeignKey(Game, related_name="votes")
    user = ForeignKey(User, related_name="game_votes")

    # Vote
    answer = CharField (Réponse soumise par le participant)

    # Timestamp
    created_at = DateTimeField (auto_now_add, indexed)
```

**Contraintes** :
```sql
-- Un seul vote par utilisateur par jeu
ALTER TABLE games_gamevote
ADD CONSTRAINT unique_vote_per_user_per_game
UNIQUE (game_id, user_id);

-- Index pour compter rapidement les votes
CREATE INDEX idx_game_answer ON games_gamevote (game_id, answer);
```

### 3. Énumérations

```python
class GameType(models.TextChoices):
    PICTURE_DESCRIPTION = "picture_description", "Picture Description"
    WORD_ASSOCIATION = "word_association", "Word Association"

class GameDifficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"

class GameStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    TIMEOUT = "TIMEOUT", "Timeout"
```

---

## Types de jeux disponibles

### 1. **Picture Description** (Description d'image)

**Objectif** : Les participants doivent identifier ou décrire une image affichée.

**Exemple de question** :
```json
{
  "id": "pd_fr_easy_01",
  "difficulty": "easy",
  "question": "Décrivez cette image : Qu'est-ce que vous voyez ?",
  "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
  "correct_answer": "montagne",
  "options": ["montagne", "plage", "ville", "forêt"],
  "context": "Une belle montagne avec de la neige au sommet"
}
```

**Niveaux de difficulté** :
- **Facile** : Identification simple (montagne, plage, ville)
- **Moyen** : Description d'ambiance ou de style architectural
- **Difficile** : Analyse détaillée, identification de période ou de contexte culturel

**Compétences travaillées** :
- Vocabulaire descriptif
- Adjectifs et expressions
- Perception visuelle et expression orale/écrite

### 2. **Word Association** (Association de mots)

**Objectif** : Associer des mots ou compléter des expressions idiomatiques.

**Exemple de question** :
```json
{
  "id": "wa_fr_easy_01",
  "difficulty": "easy",
  "question": "Quel mot associez-vous le plus à 'soleil' ?",
  "correct_answer": "chaleur",
  "options": ["chaleur", "froid", "pluie", "neige"],
  "context": "Association directe avec le soleil"
}
```

**Niveaux de difficulté** :
- **Facile** : Associations directes (soleil → chaleur)
- **Moyen** : Expressions idiomatiques ("être dans la lune")
- **Difficile** : Analogies complexes, expressions culturelles spécifiques

**Compétences travaillées** :
- Vocabulaire thématique
- Expressions idiomatiques
- Compréhension culturelle
- Associations logiques

---

## Flux de fonctionnement

### État du jeu : Machine à états

```
┌─────────┐
│ CRÉÉ    │ (Organisateur crée le jeu)
└────┬────┘
     │
     ▼
┌─────────┐
│ ACTIVE  │ ◄──── Participants votent
└────┬────┘       Timer décompte
     │
     ├─────► (Tous ont voté OU majorité atteinte)
     │            ▼
     │       ┌───────────┐
     │       │ COMPLETED │ (is_correct = True/False)
     │       └───────────┘
     │
     └─────► (Timeout expiré)
                  ▼
             ┌─────────┐
             │ TIMEOUT │ (Pas de réponse)
             └─────────┘
```

### Cycle de vie complet

```
1. CRÉATION (Organisateur uniquement)
   ├── Validation : Est organisateur ?
   ├── Validation : Événement actif (commencé, pas terminé) ?
   ├── Validation : Pas de jeu actif existant ?
   ├── Sélection aléatoire d'une question (langue + type + difficulté)
   ├── Calcul timeout_at = now + timeout_minutes
   └── Statut = ACTIVE

2. VOTE (Participants confirmés uniquement)
   ├── Validation : Jeu ACTIVE ?
   ├── Validation : Participant confirmé ?
   ├── Validation : Pas déjà voté ?
   ├── Enregistrement du vote
   └── Vérification complétion automatique

3. VÉRIFICATION COMPLÉTION (Automatique après chaque vote)
   ├── Compter les votes totaux
   ├── Compter les participants confirmés
   ├── Si tous ont voté → mark_completed()
   ├── Si majorité (>50%) pour une réponse → mark_completed()
   └── Sinon, continuer (statut ACTIVE)

4. TIMEOUT (Tâche périodique Celery)
   ├── Rechercher jeux ACTIVE avec timeout_at dépassé
   ├── Pour chaque jeu expiré → mark_timeout()
   └── Statut = TIMEOUT

5. RÉSULTATS (Disponible après COMPLETED ou TIMEOUT)
   ├── Affichage de la réponse correcte
   ├── Affichage de la réponse de l'équipe (si COMPLETED)
   ├── Statistiques : participation, distribution des votes
   └── Liste des votes individuels
```

---

## API Endpoints

Base URL : `/api/v1/games/`

### 1. Lister les jeux

```http
GET /api/v1/games/
```

**Query parameters** :
- `event_id` (optionnel) : Filtrer par événement
- `status` (optionnel) : Filtrer par statut (ACTIVE, COMPLETED, TIMEOUT)

**Permissions** : Authentifié + (Organisateur OU Participant confirmé de l'événement)

**Réponse** :
```json
[
  {
    "id": 1,
    "public_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_id": 10,
    "created_by_id": 1,
    "created_by_email": "admin@conversa.com",
    "game_type": "picture_description",
    "difficulty": "medium",
    "language_code": "fr",
    "question_id": "pd_fr_medium_01",
    "question_text": "Décrivez l'ambiance de cette scène urbaine",
    "image_url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df",
    "timeout_minutes": 5,
    "timeout_at": "2025-11-12T15:35:00Z",
    "status": "ACTIVE",
    "completed_at": null,
    "is_correct": null,
    "final_answer": null,
    "time_remaining_seconds": 180,
    "votes": [],
    "stats": {
      "total_votes": 0,
      "confirmed_participants": 8,
      "vote_counts": {},
      "votes_remaining": 8,
      "time_remaining_seconds": 180
    },
    "created_at": "2025-11-12T15:30:00Z",
    "updated_at": "2025-11-12T15:30:00Z",
    "_links": {
      "self": "/api/v1/games/1/",
      "event": "/api/v1/events/10/",
      "vote": "/api/v1/games/1/vote/"
    }
  }
]
```

### 2. Obtenir un jeu spécifique

```http
GET /api/v1/games/{id}/
```

**Permissions** : Authentifié + Accès à l'événement

**Réponse** : Même structure que ci-dessus (objet unique)

### 3. Créer un jeu

```http
POST /api/v1/games/create/
Content-Type: application/json

{
  "event_id": 10,
  "game_type": "picture_description",
  "difficulty": "medium",
  "timeout_minutes": 5
}
```

**Permissions** : Organisateur de l'événement uniquement

**Validations** :
- ✅ Utilisateur est organisateur
- ✅ Événement est publié
- ✅ Événement a commencé (datetime_start < now)
- ✅ Événement pas terminé (datetime_end > now)
- ✅ Pas de jeu actif existant pour cet événement
- ✅ Questions disponibles pour les critères (langue + type + difficulté)

**Réponse** : `201 Created` avec le jeu créé

**Erreurs** :
```json
// 403 Forbidden
{
  "detail": "Only the event organizer can create games"
}

// 400 Bad Request
{
  "event": ["This event already has an active game. Complete or timeout the current game first."]
}

// 400 Bad Request
{
  "event": ["Games can only be created after event has started"]
}
```

### 4. Voter pour un jeu

```http
POST /api/v1/games/{id}/vote/
Content-Type: application/json

{
  "answer": "animée et moderne"
}
```

**Permissions** : Participant confirmé de l'événement

**Validations** :
- ✅ Jeu est ACTIVE
- ✅ Utilisateur a une réservation CONFIRMED
- ✅ Utilisateur n'a pas déjà voté
- ✅ Réponse non vide

**Comportement** :
1. Enregistre le vote
2. Vérifie si complétion automatique (tous votés OU majorité atteinte)
3. Si oui → change statut à COMPLETED et détermine is_correct
4. Retourne le jeu mis à jour

**Réponse** : `201 Created` avec le jeu mis à jour (peut être COMPLETED)

**Erreurs** :
```json
// 403 Forbidden
{
  "detail": "Only confirmed participants can vote"
}

// 400 Bad Request
{
  "vote": ["You have already voted on this game"]
}

// 400 Bad Request
{
  "game": ["This game is no longer active"]
}
```

### 5. Obtenir les statistiques d'un jeu

```http
GET /api/v1/games/{id}/stats/
```

**Permissions** : Authentifié + Accès à l'événement

**Réponse** :
```json
{
  "total_votes": 5,
  "confirmed_participants": 8,
  "vote_counts": {
    "animée et moderne": 3,
    "calme et ancienne": 2
  },
  "votes_remaining": 3,
  "time_remaining_seconds": 120
}
```

### 6. Obtenir le jeu actif d'un événement

```http
GET /api/v1/games/active/?event_id=10
```

**Permissions** : Authentifié + Accès à l'événement

**Réponse** : Jeu actif ou `404 Not Found` si aucun jeu actif

---

## Interface utilisateur

### Architecture des composants

```
GamesComponent (Orchestrateur principal)
│
├─── État: none
│    └─── Affiche : Bouton "Créer un jeu" (si organisateur)
│                   Message d'attente (si participant)
│
├─── État: create
│    └─── <app-game-create>
│         ├─── Formulaire de sélection (type, difficulté, timeout)
│         └─── Bouton "Démarrer le jeu"
│
├─── État: play
│    └─── <app-game-play>
│         ├─── Timer en temps réel
│         ├─── Affichage de la question (+ image si applicable)
│         ├─── Formulaire de vote (si pas encore voté)
│         ├─── Message de confirmation (si déjà voté)
│         ├─── Statistiques en temps réel (polling 3s)
│         └─── Distribution des votes (barres animées)
│
├─── État: results
│    └─── <app-game-results>
│         ├─── Badge de résultat (Succès / Échec / Timeout)
│         ├─── Réponse de l'équipe vs Réponse correcte
│         ├─── Statistiques finales (taux de participation)
│         ├─── Distribution des votes avec badges
│         ├─── Liste des votes individuels
│         └─── Bouton "Créer un nouveau jeu" (si organisateur)
│
└─── Historique (collapsible)
     └─── Liste des jeux passés avec filtres visuels
```

### 1. Component : `GamesComponent` (Orchestrateur)

**Fichier** : `frontend/src/app/features/games/games.component.ts`

**Responsabilités** :
- Gestion de l'état global : `none | create | play | results`
- Chargement initial des jeux de l'événement
- Polling du jeu actif (toutes les 5 secondes)
- Gestion de l'historique des jeux
- Routage entre les sous-composants

**Inputs** :
- `eventId: number` - ID de l'événement
- `isOrganizer: boolean` - Si l'utilisateur est organisateur

**Signals** :
```typescript
currentView = signal<GameView>('none');
loading = signal(true);
error = signal<string | null>(null);
activeGame = signal<GameDto | null>(null);
completedGame = signal<GameDto | null>(null);
gameHistory = signal<GameDto[]>([]);
showHistory = signal(false);
```

**Méthodes principales** :
```typescript
loadGames(): void
  // Charge tous les jeux de l'événement
  // Détermine le jeu actif
  // Construit l'historique

startPolling(): void
  // Démarre le polling RxJS (interval 5s)
  // Vérifie les changements de statut du jeu actif

stopPolling(): void
  // Arrête le polling

onGameCreated(gameId: number): void
  // Callback après création → recharge les jeux

onGameCompleted(): void
  // Callback après complétion → affiche les résultats

startNewGame(): void
  // Affiche le formulaire de création

viewGameResults(gameId: number): void
  // Affiche les résultats d'un jeu de l'historique
```

**Polling stratégie** :
```typescript
// Polling du jeu actif
interval(5000)
  .pipe(takeWhile(() => activeGame() !== null))
  .subscribe(() => {
    gamesApi.get(activeGame()!.id).subscribe(game => {
      if (game.status !== 'ACTIVE') {
        stopPolling();
        onGameCompleted();
      }
    });
  });
```

### 2. Component : `GameCreateComponent`

**Fichier** : `frontend/src/app/features/games/components/game-create.component.ts`

**Responsabilités** :
- Affichage du formulaire de création
- Validation des sélections
- Appel API pour créer le jeu
- Émission d'événement après succès

**Inputs** :
- `eventId: number`

**Outputs** :
- `gameCreated: EventEmitter<number>` - Émet l'ID du jeu créé

**Formulaire** :
```html
<form (ngSubmit)="onCreate()">
  <select [(ngModel)]="gameType">
    <option value="picture_description">Description d'image</option>
    <option value="word_association">Association de mots</option>
  </select>

  <select [(ngModel)]="difficulty">
    <option value="easy">Facile</option>
    <option value="medium">Moyen</option>
    <option value="hard">Difficile</option>
  </select>

  <select [(ngModel)]="timeoutMinutes">
    <option [value]="3">3 minutes</option>
    <option [value]="5">5 minutes</option>
    <option [value]="10">10 minutes</option>
  </select>

  <button type="submit" [disabled]="!gameType || !difficulty">
    Démarrer le jeu
  </button>
</form>
```

### 3. Component : `GamePlayComponent`

**Fichier** : `frontend/src/app/features/games/components/game-play.component.ts`

**Responsabilités** :
- Affichage du jeu actif
- Gestion du vote
- Polling des statistiques (toutes les 3 secondes)
- Affichage du timer décompté
- Affichage des statistiques temps réel

**Inputs** :
- `gameId: number`

**Outputs** :
- `gameCompleted: EventEmitter<void>` - Émet quand le jeu se termine

**Signals** :
```typescript
game = signal<GameDto | null>(null);
stats = signal<GameStatsDto | null>(null);
loading = signal(true);
error = signal<string | null>(null);
submitting = signal(false);
hasVoted = signal(false);
```

**Polling des statistiques** :
```typescript
// Polling stats toutes les 3 secondes
interval(3000)
  .pipe(
    takeWhile(() => game()?.status === 'ACTIVE'),
    switchMap(() => gamesApi.get(gameId))
  )
  .subscribe(game => {
    this.game.set(game);
    this.stats.set(game.stats);

    if (game.status !== 'ACTIVE') {
      stopStatsPolling();
      if (game.status === 'COMPLETED') {
        gameCompleted.emit();
      }
    }
  });
```

**Affichage du timer** :
```typescript
formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Template
<div class="timer" [class.warning]="stats()?.time_remaining_seconds! < 60">
  {{ formatTime(stats()?.time_remaining_seconds || 0) }}
</div>
```

**Distribution des votes (barres animées)** :
```html
@for (entry of getVoteCountEntries(); track entry[0]) {
  <div class="vote-bar-container">
    <span class="vote-answer">{{ entry[0] }}</span>
    <div class="vote-bar-wrapper">
      <div
        class="vote-bar"
        [style.width.%]="(entry[1] / stats()!.total_votes) * 100"
      ></div>
      <span class="vote-count">{{ entry[1] }}</span>
    </div>
  </div>
}
```

### 4. Component : `GameResultsComponent`

**Fichier** : `frontend/src/app/features/games/components/game-results.component.ts`

**Responsabilités** :
- Affichage des résultats finaux
- Comparaison réponse équipe vs correcte
- Statistiques de participation
- Distribution finale des votes
- Liste des votes individuels avec avatars

**Inputs** :
- `gameId: number`

**Affichage conditionnel selon le statut** :
```html
<!-- Si COMPLETED avec succès -->
@if (game()!.status === 'COMPLETED' && game()!.is_correct) {
  <div class="result-box correct">
    <svg><!-- Checkmark --></svg>
    <h4>Bravo ! Réponse correcte</h4>
    <p>Réponse de l'équipe : {{ game()!.final_answer }}</p>
  </div>
}

<!-- Si COMPLETED avec échec -->
@if (game()!.status === 'COMPLETED' && !game()!.is_correct) {
  <div class="result-box incorrect">
    <svg><!-- X Mark --></svg>
    <h4>Dommage ! Mauvaise réponse</h4>
    <p>Réponse de l'équipe : {{ game()!.final_answer }}</p>
    <p>Réponse correcte : {{ game()!.correct_answer }}</p>
  </div>
}

<!-- Si TIMEOUT -->
@if (game()!.status === 'TIMEOUT') {
  <div class="result-box timeout">
    <svg><!-- Clock --></svg>
    <h4>Temps écoulé !</h4>
    <p>L'équipe n'a pas trouvé de consensus</p>
    <p>Réponse correcte : {{ game()!.correct_answer }}</p>
  </div>
}
```

**Statistiques avec cartes colorées** :
```html
<div class="stats-grid">
  <div class="stat-card">
    <span class="stat-label">Participants</span>
    <span class="stat-value">{{ game()!.stats.confirmed_participants }}</span>
  </div>
  <div class="stat-card">
    <span class="stat-label">Votes</span>
    <span class="stat-value">{{ game()!.stats.total_votes }}</span>
  </div>
  <div class="stat-card">
    <span class="stat-label">Taux</span>
    <span class="stat-value">{{ getParticipationRate() }}%</span>
  </div>
</div>
```

**Votes individuels avec avatars** :
```html
@for (vote of game()!.votes; track vote.id) {
  <div class="vote-item">
    <div class="vote-user">
      <div class="user-avatar">
        {{ getInitials(vote.user_email) }}
      </div>
      <span class="user-email">{{ vote.user_email }}</span>
    </div>
    <div class="vote-answer-box">
      <span>{{ vote.answer }}</span>
      @if (vote.answer === game()!.correct_answer) {
        <svg class="vote-check"><!-- Checkmark --></svg>
      }
    </div>
  </div>
}
```

### 5. Service : `GamesApiService`

**Fichier** : `frontend/src/app/core/http/services/games-api.service.ts`

**Méthodes** :
```typescript
list(params?: GameListParams): Observable<GameDto[]>
  // GET /api/v1/games/
  // Filters: event_id, status

get(id: number): Observable<GameDto>
  // GET /api/v1/games/{id}/

create(payload: GameCreatePayload): Observable<GameDto>
  // POST /api/v1/games/create/

vote(gameId: number, payload: VoteSubmitPayload): Observable<GameDto>
  // POST /api/v1/games/{gameId}/vote/

getStats(gameId: number): Observable<GameStatsDto>
  // GET /api/v1/games/{gameId}/stats/

getActiveGame(eventId: number): Observable<GameDto>
  // GET /api/v1/games/active/?event_id={eventId}
```

---

## Règles métier

### 1. Permissions et accès

| Action | Rôle requis | Condition supplémentaire |
|--------|-------------|--------------------------|
| **Créer un jeu** | Organisateur de l'événement | Événement actif (commencé, pas terminé) + Pas de jeu actif existant |
| **Voter** | Participant | Réservation CONFIRMED + Pas déjà voté + Jeu ACTIVE |
| **Voir les jeux** | Organisateur OU Participant confirmé | Accès à l'événement |
| **Voir les statistiques** | Organisateur OU Participant confirmé | Accès à l'événement |
| **Voir les résultats** | Organisateur OU Participant confirmé | Accès à l'événement |

### 2. Règles de création

```python
# GameService.create_game()

✅ VALIDE SI :
- user.id == event.organizer_id OR user.is_staff
- event.status == Event.Status.PUBLISHED
- event.datetime_start < timezone.now() < event.datetime_end
- NOT exists Game(event=event, status=ACTIVE)
- Questions disponibles pour (language, game_type, difficulty)

❌ REFUSE SI :
- Utilisateur pas organisateur → PermissionDenied
- Événement pas publié → ValidationError
- Événement pas commencé ou déjà fini → ValidationError
- Jeu actif existant → ValidationError
- Pas de questions disponibles → ValidationError (FileNotFoundError)
```

### 3. Règles de vote

```python
# GameService.submit_vote()

✅ VALIDE SI :
- game.status == GameStatus.ACTIVE
- exists Booking(event=game.event, user=user, status=CONFIRMED)
- NOT exists GameVote(game=game, user=user)
- answer.strip() != ""

❌ REFUSE SI :
- Jeu pas ACTIVE → ValidationError
- Pas de réservation confirmée → PermissionDenied
- Déjà voté → ValidationError
- Réponse vide → ValidationError
```

### 4. Règles de complétion automatique

```python
# GameService._check_and_complete_game()

def _check_and_complete_game(game) -> bool:
    votes = GameVote.objects.filter(game=game)
    total_votes = votes.count()
    confirmed_count = Booking.objects.filter(
        event=game.event,
        status=CONFIRMED
    ).count()

    # Compter les votes par réponse
    vote_counts = Counter(votes.values_list('answer', flat=True))
    most_common_answer, most_common_count = vote_counts.most_common(1)[0]

    # CONDITION 1 : Tous les participants ont voté
    if total_votes >= confirmed_count:
        is_correct = (most_common_answer == game.correct_answer)
        game.mark_completed(is_correct, most_common_answer)
        return True

    # CONDITION 2 : Majorité stricte (>50%) pour une réponse
    if most_common_count > (confirmed_count / 2):
        is_correct = (most_common_answer == game.correct_answer)
        game.mark_completed(is_correct, most_common_answer)
        return True

    return False
```

**Exemples** :

| Confirmés | Votes | Réponse A | Réponse B | Résultat |
|-----------|-------|-----------|-----------|----------|
| 8 | 8 | 5 | 3 | ✅ COMPLETED (A gagne, tous ont voté) |
| 8 | 5 | 5 | 0 | ✅ COMPLETED (A gagne, majorité >50% = >4) |
| 8 | 4 | 4 | 0 | ⏳ CONTINUE (4 votes, mais besoin >4 pour majorité) |
| 8 | 6 | 3 | 3 | ⏳ CONTINUE (Égalité, pas de majorité) |
| 10 | 10 | 5 | 5 | ✅ COMPLETED (Tous ont voté, A gagne par ordre d'insertion) |

### 5. Règles de timeout

**Tâche Celery périodique** : Exécutée toutes les 30 secondes

```python
# backend/games/tasks.py

@shared_task
def check_game_timeouts():
    """Vérifie et marque les jeux expirés"""
    expired_games = Game.objects.filter(
        status=GameStatus.ACTIVE,
        timeout_at__lte=timezone.now()
    )

    count = 0
    for game in expired_games:
        game.mark_timeout()
        count += 1

        # Log d'audit
        AuditService.log_action(
            user=game.event.organizer,
            action='UPDATE',
            model_name='Game',
            object_id=game.id,
            changes={
                'status': {'old': 'ACTIVE', 'new': 'TIMEOUT'},
                'reason': 'Automatic timeout'
            }
        )

    return f"Marked {count} games as timeout"
```

**Configuration Celery Beat** :
```python
# backend/config/celery.py

app.conf.beat_schedule = {
    'check-game-timeouts': {
        'task': 'games.tasks.check_game_timeouts',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
}
```

---

## Gestion du contenu

### Structure des fichiers JSON

**Emplacement** : `backend/fixtures/games/`

**Nomenclature** : `{game_type}_{language_code}.json`

**Fichiers disponibles** :
```
backend/fixtures/games/
├── picture_description_fr.json
├── picture_description_en.json
├── picture_description_nl.json
├── word_association_fr.json
├── word_association_en.json
└── word_association_nl.json
```

### Format JSON des questions

**Picture Description** :
```json
[
  {
    "id": "pd_fr_easy_01",
    "difficulty": "easy",
    "question": "Décrivez cette image : Qu'est-ce que vous voyez ?",
    "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
    "correct_answer": "montagne",
    "options": ["montagne", "plage", "ville", "forêt"],
    "context": "Une belle montagne avec de la neige au sommet"
  }
]
```

**Word Association** :
```json
[
  {
    "id": "wa_fr_easy_01",
    "difficulty": "easy",
    "question": "Quel mot associez-vous le plus à 'soleil' ?",
    "correct_answer": "chaleur",
    "options": ["chaleur", "froid", "pluie", "neige"],
    "context": "Association directe avec le soleil"
  }
]
```

**Champs** :
- `id` : Identifiant unique (format: `{type}_{lang}_{difficulty}_{number}`)
- `difficulty` : `easy` | `medium` | `hard`
- `question` : Texte de la question
- `correct_answer` : Réponse correcte attendue
- `options` : Liste des options proposées (utilisé pour validation future)
- `image_url` : URL de l'image (optionnel, uniquement pour picture_description)
- `context` : Description pour les créateurs de contenu (non affiché aux utilisateurs)

### Chargement et cache

```python
# GameService._load_game_content()

_game_content_cache: Dict[str, List[Dict]] = {}

@staticmethod
def _load_game_content(language_code: str, game_type: str) -> List[Dict]:
    cache_key = f"{language_code}_{game_type}"

    # Vérifier le cache
    if cache_key in GameService._game_content_cache:
        return GameService._game_content_cache[cache_key]

    # Charger depuis le fichier
    file_path = Path(settings.BASE_DIR) / "fixtures" / "games" / f"{game_type}_{language_code}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Game content file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    # Mettre en cache
    GameService._game_content_cache[cache_key] = content
    return content
```

**Cache en mémoire** : Les questions sont chargées une seule fois au démarrage et restent en mémoire pour performance.

### Sélection aléatoire

```python
# GameService._get_random_question()

@staticmethod
def _get_random_question(language_code: str, game_type: str, difficulty: str) -> Dict:
    questions = GameService._load_game_content(language_code, game_type)

    # Filtrer par difficulté
    filtered = [q for q in questions if q.get("difficulty") == difficulty]

    if not filtered:
        raise ValidationError({
            "difficulty": f"No questions available for {game_type} at {difficulty} level in {language_code}"
        })

    # Sélection aléatoire
    return random.choice(filtered)
```

### Ajout de nouvelles questions

**Processus** :
1. Identifier le fichier concerné (type + langue)
2. Respecter le format JSON
3. Générer un `id` unique : `{type}_{lang}_{difficulty}_{number}`
4. Assurer la cohérence des `options` avec `correct_answer`
5. Pour `picture_description`, fournir une `image_url` valide (Unsplash recommandé)
6. Tester en créant un jeu avec cette difficulté
7. **Pas besoin de redémarrer** : Le cache se met à jour au prochain chargement

**Exemple d'ajout** :
```json
{
  "id": "pd_fr_hard_05",
  "difficulty": "hard",
  "question": "Identifiez le mouvement architectural représenté dans cette structure",
  "image_url": "https://images.unsplash.com/photo-1234567890",
  "correct_answer": "brutalisme",
  "options": ["brutalisme", "modernisme", "déconstructivisme", "postmodernisme"],
  "context": "Bâtiment brutaliste des années 1970 avec béton apparent"
}
```

---

## Système de vote et complétion

### Algorithme de détection de majorité

```python
from collections import Counter

def _check_and_complete_game(game) -> bool:
    # 1. Récupérer tous les votes
    votes = GameVote.objects.filter(game=game).values_list('answer', flat=True)
    total_votes = len(votes)

    if total_votes == 0:
        return False

    # 2. Compter les participants confirmés
    confirmed_count = game.event.bookings.filter(
        status=BookingStatus.CONFIRMED
    ).count()

    # 3. Compter les votes par réponse
    vote_counts = Counter(votes)
    most_common_answer, most_common_count = vote_counts.most_common(1)[0]

    # 4. RÈGLE 1 : Tous les participants ont voté
    if total_votes >= confirmed_count:
        is_correct = (most_common_answer == game.correct_answer)
        game.mark_completed(is_correct=is_correct, final_answer=most_common_answer)
        return True

    # 5. RÈGLE 2 : Majorité stricte (>50%)
    majority_threshold = confirmed_count / 2
    if most_common_count > majority_threshold:
        is_correct = (most_common_answer == game.correct_answer)
        game.mark_completed(is_correct=is_correct, final_answer=most_common_answer)
        return True

    return False
```

### Cas particuliers

**Égalité parfaite** :
```python
# 10 participants, 5 votes "A", 5 votes "B"
# → most_common(1) retourne le premier par ordre d'insertion
# → Si tous ont voté, "A" est choisi (arbitraire)
```

**Solution recommandée** : En cas d'égalité et tous ayant voté, marquer le jeu comme TIMEOUT plutôt que de choisir arbitrairement.

```python
# Amélioration suggérée
vote_counts = Counter(votes)
top_2 = vote_counts.most_common(2)

if len(top_2) == 2 and top_2[0][1] == top_2[1][1]:
    # Égalité entre les 2 réponses les plus votées
    if total_votes >= confirmed_count:
        # Tous ont voté mais égalité → Timeout
        game.mark_timeout()
        return True
```

### Performance et optimisation

**Index de comptage** :
```sql
CREATE INDEX idx_game_answer ON games_gamevote (game_id, answer);
```

**Requête optimisée** :
```python
# Compter en base de données plutôt qu'en Python
vote_counts = GameVote.objects.filter(game=game).values('answer').annotate(
    count=Count('id')
).order_by('-count')
```

---

## Scénarios d'utilisation

### Scénario 1 : Jeu avec complétion par majorité

**Contexte** :
- Événement avec 10 participants confirmés
- Organisateur crée un jeu "Picture Description" niveau moyen
- Timeout : 5 minutes

**Déroulement** :

```
T+0s    [Organisateur] Crée le jeu
        → Status: ACTIVE
        → timeout_at = T+300s

T+10s   [Participant 1] Vote: "animée et moderne"
        → Vérification: 1/10 votes, pas de majorité
        → Status: ACTIVE

T+15s   [Participant 2] Vote: "animée et moderne"
        → Vérification: 2/10 votes, pas de majorité
        → Status: ACTIVE

T+20s   [Participant 3] Vote: "calme et ancienne"
        → Vérification: 3/10 votes, "animée et moderne" = 2 (20%), pas de majorité
        → Status: ACTIVE

...

T+90s   [Participant 6] Vote: "animée et moderne"
        → Vérification: 6/10 votes, "animée et moderne" = 6 (60%)
        → 6 > (10/2) → MAJORITÉ ATTEINTE ✅
        → final_answer = "animée et moderne"
        → is_correct = True (correct_answer match)
        → Status: COMPLETED
        → completed_at = T+90s

T+95s   [Frontend] Polling détecte status COMPLETED
        → Affiche GameResultsComponent
        → Badge "Bravo ! Réponse correcte"
```

**Résultat final** :
- ✅ Jeu terminé en 90 secondes (avant timeout)
- ✅ Réponse correcte trouvée
- ✅ 4 participants n'ont pas voté (pas nécessaire grâce à la majorité)

### Scénario 2 : Jeu avec timeout

**Contexte** :
- Événement avec 8 participants confirmés
- Organisateur crée un jeu "Word Association" niveau difficile
- Timeout : 3 minutes

**Déroulement** :

```
T+0s    [Organisateur] Crée le jeu
        → Status: ACTIVE
        → timeout_at = T+180s

T+20s   [Participant 1] Vote: "rouge"
        → Vérification: 1/8 votes, pas de majorité
        → Status: ACTIVE

T+45s   [Participant 2] Vote: "bleu"
        → Vérification: 2/8 votes, égalité, pas de majorité
        → Status: ACTIVE

T+70s   [Participant 3] Vote: "rouge"
        → Vérification: 3/8 votes, "rouge" = 2 (25%), pas de majorité (besoin >4)
        → Status: ACTIVE

T+120s  [Participant 4] Vote: "vert"
        → Vérification: 4/8 votes, "rouge" = 2 (25%), pas de majorité
        → Status: ACTIVE

T+180s  [Celery Task] check_game_timeouts() s'exécute
        → Trouve game avec timeout_at <= now et status ACTIVE
        → game.mark_timeout()
        → Status: TIMEOUT
        → completed_at = T+180s

T+185s  [Frontend] Polling détecte status TIMEOUT
        → Affiche GameResultsComponent
        → Badge "Temps écoulé !"
        → Affiche la réponse correcte sans final_answer
```

**Résultat final** :
- ⏱️ Jeu terminé par timeout
- ❌ Pas de réponse de l'équipe (pas de majorité)
- ℹ️ 4/8 participants ont voté (50% de participation)
- ℹ️ Distribution : rouge (2), bleu (1), vert (1)

### Scénario 3 : Jeu avec tous les participants ayant voté

**Contexte** :
- Événement avec 5 participants confirmés
- Organisateur crée un jeu "Picture Description" niveau facile
- Timeout : 10 minutes

**Déroulement** :

```
T+0s    [Organisateur] Crée le jeu
        → Question: "Qu'est-ce que vous voyez ?"
        → correct_answer: "montagne"
        → Status: ACTIVE

T+10s   [Participant 1] Vote: "montagne"
T+15s   [Participant 2] Vote: "montagne"
T+20s   [Participant 3] Vote: "plage"
T+25s   [Participant 4] Vote: "montagne"
T+30s   [Participant 5] Vote: "montagne"

        → Vérification: 5/5 votes = 100% (tous ont voté)
        → "montagne" = 4 votes (80%)
        → final_answer = "montagne"
        → is_correct = True
        → Status: COMPLETED
        → completed_at = T+30s
```

**Résultat final** :
- ✅ Jeu terminé en 30 secondes (tous ont voté)
- ✅ Réponse correcte trouvée
- ✅ 100% de participation
- ✅ 80% de consensus sur la bonne réponse

### Scénario 4 : Tentative de création avec jeu actif existant

**Contexte** :
- Événement en cours avec un jeu ACTIVE
- Organisateur tente de créer un nouveau jeu

**Déroulement** :

```
[Organisateur] POST /api/v1/games/create/
{
  "event_id": 10,
  "game_type": "word_association",
  "difficulty": "easy",
  "timeout_minutes": 5
}

[Backend] GameService.create_game()
  → _validate_no_active_game(event)
  → Game.objects.filter(event=event, status=ACTIVE).exists() = True
  → ❌ Raise ValidationError

[Response] 400 Bad Request
{
  "event": ["This event already has an active game. Complete or timeout the current game first."]
}

[Frontend] Affiche l'erreur
  → "Un jeu est déjà en cours. Attendez sa fin pour créer un nouveau jeu."
```

### Scénario 5 : Tentative de vote multiple

**Contexte** :
- Participant essaie de voter deux fois pour le même jeu

**Déroulement** :

```
[Participant] POST /api/v1/games/5/vote/
{
  "answer": "montagne"
}

[Backend] Vote créé avec succès
  → GameVote(game=5, user=2, answer="montagne")

[Participant] POST /api/v1/games/5/vote/ (deuxième tentative)
{
  "answer": "plage"
}

[Backend] GameService.submit_vote()
  → GameVote.objects.filter(game=game, user=user).first() != None
  → ❌ Raise ValidationError

[Response] 400 Bad Request
{
  "vote": ["You have already voted on this game"]
}

[Frontend] Affiche l'erreur
  → "Vous avez déjà voté pour ce jeu"
```

---

## Annexes

### A. Requêtes SQL importantes

**Compter les votes par réponse** :
```sql
SELECT answer, COUNT(*) as vote_count
FROM games_gamevote
WHERE game_id = 1
GROUP BY answer
ORDER BY vote_count DESC;
```

**Trouver les jeux expirés** :
```sql
SELECT id, event_id, timeout_at
FROM games_game
WHERE status = 'ACTIVE'
  AND timeout_at <= NOW();
```

**Statistiques d'un jeu** :
```sql
SELECT
  g.id,
  g.status,
  COUNT(DISTINCT gv.id) as total_votes,
  COUNT(DISTINCT b.id) as confirmed_participants,
  (COUNT(DISTINCT gv.id)::float / COUNT(DISTINCT b.id)::float * 100) as participation_rate
FROM games_game g
LEFT JOIN games_gamevote gv ON gv.game_id = g.id
LEFT JOIN bookings_booking b ON b.event_id = g.event_id AND b.status = 'CONFIRMED'
WHERE g.id = 1
GROUP BY g.id;
```

**Historique des jeux d'un événement** :
```sql
SELECT
  id,
  game_type,
  difficulty,
  status,
  is_correct,
  created_at,
  completed_at
FROM games_game
WHERE event_id = 10
ORDER BY created_at DESC;
```

### B. Variables d'environnement

**Settings Django** :
```python
# settings/base.py

GAMES_DEFAULT_TIMEOUT_MINUTES = 5
GAMES_MIN_TIMEOUT_MINUTES = 1
GAMES_MAX_TIMEOUT_MINUTES = 30
GAMES_CONTENT_PATH = BASE_DIR / "fixtures" / "games"
```

### C. Monitoring et métriques

**Métriques à surveiller** :

1. **Taux de participation moyen** :
   ```sql
   SELECT AVG(participation_rate)
   FROM (
     SELECT (COUNT(DISTINCT gv.id)::float / COUNT(DISTINCT b.id)::float) as participation_rate
     FROM games_game g
     LEFT JOIN games_gamevote gv ON gv.game_id = g.id
     LEFT JOIN bookings_booking b ON b.event_id = g.event_id AND b.status = 'CONFIRMED'
     WHERE g.status IN ('COMPLETED', 'TIMEOUT')
     GROUP BY g.id
   ) subquery;
   ```

2. **Taux de réussite** :
   ```sql
   SELECT
     (COUNT(CASE WHEN is_correct = TRUE THEN 1 END)::float / COUNT(*)::float * 100) as success_rate
   FROM games_game
   WHERE status = 'COMPLETED';
   ```

3. **Durée moyenne des jeux** :
   ```sql
   SELECT
     AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
   FROM games_game
   WHERE status IN ('COMPLETED', 'TIMEOUT')
     AND completed_at IS NOT NULL;
   ```

4. **Popularité des types de jeux** :
   ```sql
   SELECT game_type, COUNT(*) as count
   FROM games_game
   GROUP BY game_type
   ORDER BY count DESC;
   ```

### D. Tests recommandés

**Backend tests** : `backend/games/tests/`

```python
# test_services.py

def test_create_game_success(organizer, active_event):
    """Test création réussie d'un jeu"""
    game = GameService.create_game(
        event=active_event,
        created_by=organizer,
        game_type='picture_description',
        difficulty='medium',
        timeout_minutes=5
    )
    assert game.status == GameStatus.ACTIVE
    assert game.question_text is not None

def test_create_game_with_active_game_fails(organizer, active_event):
    """Test échec si jeu actif existant"""
    GameService.create_game(active_event, organizer, 'picture_description', 'easy', 5)

    with pytest.raises(ValidationError) as exc:
        GameService.create_game(active_event, organizer, 'word_association', 'easy', 5)

    assert 'already has an active game' in str(exc.value)

def test_vote_triggers_completion_at_majority(game, participants):
    """Test complétion automatique à la majorité"""
    # 10 participants, 6 votent pour "A"
    for i in range(6):
        GameService.submit_vote(game, participants[i], "A")

    game.refresh_from_db()
    assert game.status == GameStatus.COMPLETED
    assert game.final_answer == "A"

def test_vote_after_timeout_fails(expired_game, participant):
    """Test échec de vote après timeout"""
    with pytest.raises(ValidationError) as exc:
        GameService.submit_vote(expired_game, participant, "answer")

    assert 'no longer active' in str(exc.value)
```

**Frontend tests** : `frontend/src/app/features/games/`

```typescript
// game-play.component.spec.ts

describe('GamePlayComponent', () => {
  it('should display timer countdown', () => {
    component.stats.set({ time_remaining_seconds: 120, ... });
    expect(component.formatTime(120)).toBe('2:00');
  });

  it('should show warning when less than 60 seconds', () => {
    component.stats.set({ time_remaining_seconds: 45, ... });
    fixture.detectChanges();
    const timer = fixture.nativeElement.querySelector('.timer');
    expect(timer.classList.contains('warning')).toBe(true);
  });

  it('should disable vote button after voting', async () => {
    component.hasVoted.set(true);
    fixture.detectChanges();
    const voteSection = fixture.nativeElement.querySelector('.voting-section');
    expect(voteSection).toBeNull();
  });

  it('should emit gameCompleted when status changes to COMPLETED', (done) => {
    component.gameCompleted.subscribe(() => {
      expect(true).toBe(true);
      done();
    });

    const completedGame = { ...mockGame, status: 'COMPLETED' };
    gamesApi.get = jasmine.createSpy().and.returnValue(of(completedGame));
    component.loadGame();
  });
});
```

### E. Roadmap future

**Fonctionnalités prévues** :

1. **Nouveaux types de jeux** :
   - ✅ Picture Description (Implémenté)
   - ✅ Word Association (Implémenté)
   - 🔄 Debate (Prévu - arguments pour/contre)
   - 🔄 Role Play (Prévu - improvisation de dialogues)

2. **Améliorations du système de vote** :
   - Options de vote : choix multiples prédéfinis vs réponse libre
   - Validation des réponses (accepter synonymes/variations)
   - Système de points individuels

3. **Fonctionnalités sociales** :
   - Commentaires après le jeu
   - Réactions aux votes des autres
   - Classement des participants

4. **Analytics** :
   - Dashboard organisateur : statistiques détaillées
   - Progression des participants au fil des événements
   - Recommandations de difficulté adaptative

5. **Notifications temps réel** :
   - WebSocket pour mises à jour instantanées (remplacer polling)
   - Push notifications : "Nouveau jeu créé !"
   - Alertes : "Plus que 1 minute !"

---

## Conclusion

Le système de jeux collaboratifs de Conversa offre une expérience interactive complète pour l'apprentissage des langues en groupe. Grâce à une architecture solide (service layer + REST API + composants Angular standalone) et des règles métier bien définies, le système garantit :

- ✅ **Fiabilité** : Validations strictes, contraintes DB, gestion des erreurs
- ✅ **Performance** : Cache des questions, index DB, polling optimisé
- ✅ **Expérience utilisateur** : Temps réel, statistiques visuelles, historique
- ✅ **Extensibilité** : Ajout facile de nouveaux types de jeux et langues

**Contact** : Pour toute question technique, contacter l'équipe backend Conversa.

---

*Documentation générée le 2025-11-12 | Version 1.0*
