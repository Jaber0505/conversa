# Démonstration du bon fonctionnement de l'application Conversa

## Table des matières

1. [Fonctionnalités Business Principales](#1-fonctionnalités-business-principales)
   - [Point de vue Membre](#11-point-de-vue-membre)
   - [Point de vue Administrateur](#12-point-de-vue-administrateur)
2. [Autres Fonctionnalités Pertinentes](#2-autres-fonctionnalités-pertinentes)
   - [Système de Paiement Stripe](#21-système-de-paiement-stripe)
   - [Gestion des Réservations](#22-gestion-des-réservations)
   - [Système d'Audit](#23-système-daudit)
3. [Multilinguisme](#3-multilinguisme)
4. [Démonstration API](#4-démonstration-api)
   - [Endpoints GET](#41-endpoints-get)
   - [Endpoints POST/PUT/DELETE](#42-endpoints-postputdelete)
5. [Procédure de Désinscription](#5-procédure-de-désinscription)

---

## 1. Fonctionnalités Business Principales

### 1.1 Point de vue Membre

#### Réservation d'un Événement avec Paiement

**Objectif** : Permettre à un membre de réserver et payer une place pour un événement linguistique.

**Prérequis** : Utilisateur connecté (Marie Dupont)

**Démonstration** :

1. **Navigation vers la liste des événements**
   - Navigateur 1 : Chrome (pour le membre Marie)
   - URL : `http://localhost:4200/fr/events`
   - Affichage de tous les événements publiés disponibles

2. **Sélection d'un événement**
   - Cliquer sur "Voir détails" d'un événement
   - URL : `http://localhost:4200/fr/events/1`
   - Affichage des détails :
     ```
     - Titre : "Échange linguistique Français-Anglais"
     - Date : 15 décembre 2025 à 19h00
     - Lieu : 123 Rue de la Paix, 75002 Paris (avec carte interactive)
     - Organisateur : Admin Conversa
     - Places restantes : 12/20
     - Prix : 15,00 EUR
     - Description complète
     - Langues pratiquées : Français, Anglais
     - Configuration du jeu : Speed Meeting (10 min/round, 6 rounds)
     ```

3. **Réservation**
   - Cliquer sur "Réserver ma place"
   - ✅ Création d'une réservation en statut PENDING
   - ✅ Redirection automatique vers Stripe Checkout

4. **Paiement Stripe**
   ```
   Page de paiement Stripe Checkout :
   - Montant : 15.00 EUR
   - Description : Réservation pour "Échange linguistique Français-Anglais"
   - Carte de test : 4242 4242 4242 4242
   - Date d'expiration : 12/34
   - CVC : 123
   - Code postal : 75002
   ```

5. **Confirmation**
   - ✅ Paiement réussi sur Stripe
   - ✅ Webhook Stripe reçu : `payment_intent.succeeded`
   - ✅ Statut de la réservation : PENDING → CONFIRMED
   - ✅ Place réservée décrémentée (12 → 11 places restantes)
   - ✅ Redirection vers la page de succès
   - ✅ Message : "Votre réservation a été confirmée ! Un email de confirmation vous a été envoyé."

**Code Backend - Création de la réservation** : `backend/bookings/services/booking_service.py`
```python
@staticmethod
@transaction.atomic
def create_booking(user, event):
    """Create a new booking for an event."""
    # Vérification de la disponibilité
    if not EventService.check_availability(event):
        raise ValidationError("No more seats available")

    # Vérification des doublons
    if Booking.objects.filter(user=user, event=event,
                              status=BookingStatus.CONFIRMED).exists():
        raise ValidationError("You already have a confirmed booking for this event")

    # Création de la réservation en statut PENDING
    booking = Booking.objects.create(
        user=user,
        event=event,
        status=BookingStatus.PENDING,
        amount=event.price
    )

    # Log d'audit
    AuditService.log_action(
        user=user,
        action='CREATE',
        model_name='Booking',
        object_id=booking.id,
        changes={'status': 'PENDING', 'amount': str(event.price)}
    )

    return booking
```

**Code Backend - Webhook Stripe** : `backend/payments/views.py`
```python
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        booking_id = payment_intent['metadata']['booking_id']

        # Confirmation automatique de la réservation
        booking = Booking.objects.get(id=booking_id)
        booking.status = BookingStatus.CONFIRMED
        booking.payment_intent_id = payment_intent['id']
        booking.save()

        # Décrémentation du nombre de places disponibles
        booking.event.current_participants += 1
        booking.event.save()

        # Envoi de l'email de confirmation
        send_booking_confirmation_email(booking)

        # Log d'audit
        AuditService.log_action(
            user=booking.user,
            action='UPDATE',
            model_name='Booking',
            object_id=booking.id,
            changes={'status': {'old': 'PENDING', 'new': 'CONFIRMED'}}
        )

    return HttpResponse(status=200)
```

**Base de données - Impact** :
```sql
-- Table: bookings_booking
INSERT INTO bookings_booking (user_id, event_id, status, amount, payment_intent_id, created_at)
VALUES (2, 1, 'CONFIRMED', 15.00, 'pi_1ABC123xyz', NOW());

-- Table: events_event (mise à jour du compteur)
UPDATE events_event
SET current_participants = current_participants + 1
WHERE id = 1;

-- Table: audit_auditlog
INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
VALUES (2, 'CREATE', 'Booking', 1, '{"status": "CONFIRMED", "amount": "15.00"}', NOW());
```

#### Visualisation et Gestion des Réservations

**Objectif** : Permettre au membre de voir toutes ses réservations et les gérer.

**Démonstration** :

1. **Accès à "Mes Réservations"**
   - URL : `http://localhost:4200/fr/bookings`
   - Affichage de toutes les réservations de Marie

2. **Informations affichées**
   ```
   Réservation #1 - Statut: CONFIRMED ✅
   - Événement : Échange linguistique Français-Anglais
   - Date : 15 décembre 2025 à 19h00
   - Lieu : 123 Rue de la Paix, 75002 Paris
   - Montant payé : 15,00 EUR
   - Actions : Voir détails | Annuler

   Réservation #2 - Statut: CANCELLED ❌
   - Événement : Conversation Espagnol débutants
   - Date : 20 novembre 2025 à 18h30
   - Montant remboursé : 12,00 EUR
   - Raison : Annulé par l'utilisateur
   ```

3. **Annulation d'une réservation**
   - Cliquer sur "Annuler" pour la réservation #1
   - ⚠️ Vérification : l'événement a lieu dans plus de 24h
   - Confirmation : "Êtes-vous sûr de vouloir annuler cette réservation ?"
   - ✅ Statut : CONFIRMED → CANCELLED
   - ✅ Remboursement automatique via Stripe
   - ✅ Place libérée (11 → 12 places disponibles)
   - ✅ Email de confirmation d'annulation envoyé

**Code Backend - Annulation de réservation** : `backend/bookings/services/booking_service.py`
```python
@staticmethod
@transaction.atomic
def cancel_booking(booking):
    """Cancel a booking and process refund."""
    if booking.status != BookingStatus.CONFIRMED:
        raise ValidationError("Only confirmed bookings can be cancelled")

    # Vérification : au moins 24h avant l'événement
    time_until_event = booking.event.date - timezone.now()
    if time_until_event.total_seconds() < 86400:  # 24 heures
        raise ValidationError("Cannot cancel booking less than 24 hours before event")

    # Remboursement via Stripe
    if booking.payment_intent_id:
        try:
            refund = stripe.Refund.create(
                payment_intent=booking.payment_intent_id,
                reason='requested_by_customer'
            )
            booking.refund_id = refund['id']
        except stripe.error.StripeError as e:
            logger.error(f"Refund failed: {e}")
            raise ValidationError(f"Refund failed: {str(e)}")

    # Mise à jour du statut
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save()

    # Libération de la place
    booking.event.current_participants -= 1
    booking.event.save()

    # Email de confirmation
    send_booking_cancellation_email(booking)

    # Log d'audit
    AuditService.log_action(
        user=booking.user,
        action='UPDATE',
        model_name='Booking',
        object_id=booking.id,
        changes={'status': {'old': 'CONFIRMED', 'new': 'CANCELLED'}}
    )

    return booking
```

---

### 1.2 Point de vue Administrateur

#### Création et Publication d'un Événement

**Objectif** : Permettre à un administrateur de créer et publier des événements linguistiques.

**Prérequis** : Utilisateur staff connecté (Admin Conversa)

**Démonstration** :

1. **Navigation vers la création d'événement**
   - Navigateur 2 : Firefox (pour l'administrateur)
   - URL : `http://localhost:4200/fr/events/create`
   - ⚠️ Page accessible uniquement aux utilisateurs `is_staff=True`

2. **Remplissage du formulaire**
   ```
   Informations générales :
   - Titre : "Soirée Espagnol-Français"
   - Description : "Venez pratiquer l'espagnol dans une ambiance conviviale autour de tapas et de sangria. Tous niveaux bienvenus !"
   - Date : 20 décembre 2025
   - Heure : 20:00

   Lieu :
   - Adresse : "45 Rue du Faubourg Saint-Antoine, 75011 Paris, France"
   - Latitude : 48.8530 (auto-complété via API de géocodage)
   - Longitude : 2.3726 (auto-complété via API de géocodage)

   Détails :
   - Prix : 18.00 EUR
   - Nombre maximum de participants : 15
   - Langues pratiquées :
     * Principale : Espagnol (es)
     * Secondaire : Français (fr)

   Configuration du jeu (optionnel) :
   - Jeu sélectionné : "Conversation en Rond"
   - Durée des rounds : 15 minutes
   - Nombre de rounds : 4
   ```

3. **Sauvegarde en brouillon**
   - Cliquer sur "Sauvegarder le brouillon"
   - ✅ Événement créé avec statut DRAFT
   - ✅ Message de confirmation : "Événement sauvegardé en brouillon"
   - ✅ Événement non visible pour les membres (uniquement pour l'organisateur)

4. **Prévisualisation**
   - Bouton "Prévisualiser" disponible
   - Affichage de l'événement tel qu'il apparaîtra aux membres
   - Possibilité de modifier avant publication

5. **Publication de l'événement**
   - Cliquer sur "Publier l'événement"
   - ✅ Vérifications automatiques effectuées :
     * Tous les champs obligatoires remplis ✓
     * Date dans le futur ✓
     * Prix supérieur à 0 ✓
     * Nombre de places > 0 ✓
     * Au moins une langue sélectionnée ✓
   - ✅ Statut : DRAFT → PUBLISHED
   - ✅ Événement maintenant visible pour tous les membres
   - ✅ Date de publication enregistrée
   - ✅ Message : "Événement publié avec succès !"

**Code Backend - Création d'événement** : `backend/events/services/event_service.py`
```python
@staticmethod
@transaction.atomic
def create_event(organizer, title, description, date, location,
                 price, max_participants, languages, game_config=None):
    """Create a new event."""
    # Validation : date dans le futur
    if date < timezone.now():
        raise ValidationError("Event date must be in the future")

    # Validation : prix positif
    if price <= 0:
        raise ValidationError("Price must be greater than 0")

    # Validation : participants minimum
    if max_participants <= 0:
        raise ValidationError("Max participants must be greater than 0")

    # Création de l'événement en mode DRAFT
    event = Event.objects.create(
        organizer=organizer,
        title=title,
        description=description,
        date=date,
        location=location,
        price=price,
        max_participants=max_participants,
        current_participants=0,
        status=Event.Status.DRAFT,
        game_config=game_config or {}
    )

    # Association des langues (relation ManyToMany)
    event.languages.set(languages)

    # Log d'audit
    AuditService.log_action(
        user=organizer,
        action='CREATE',
        model_name='Event',
        object_id=event.id,
        changes={'status': 'DRAFT', 'title': title}
    )

    return event
```

**Code Backend - Publication d'événement** : `backend/events/services/event_service.py`
```python
@staticmethod
@transaction.atomic
def publish_event(event):
    """Publish a draft event."""
    # Vérifications avant publication
    if event.status != Event.Status.DRAFT:
        raise ValidationError("Only draft events can be published")

    if not event.title or not event.description:
        raise ValidationError("Title and description are required")

    if event.date < timezone.now():
        raise ValidationError("Cannot publish event with past date")

    if event.price <= 0:
        raise ValidationError("Price must be greater than 0")

    if event.max_participants <= 0:
        raise ValidationError("Max participants must be greater than 0")

    if event.languages.count() == 0:
        raise ValidationError("At least one language is required")

    # Publication
    event.status = Event.Status.PUBLISHED
    event.published_at = timezone.now()
    event.save()

    # Log d'audit
    AuditService.log_action(
        user=event.organizer,
        action='UPDATE',
        model_name='Event',
        object_id=event.id,
        changes={'status': {'old': 'DRAFT', 'new': 'PUBLISHED'}}
    )

    return event
```

**Base de données - Impact** :
```sql
-- Création en brouillon
INSERT INTO events_event (
    organizer_id, title, description, date, location,
    price, max_participants, current_participants, status,
    game_config, created_at
)
VALUES (
    1,
    'Soirée Espagnol-Français',
    'Venez pratiquer l''espagnol...',
    '2025-12-20 20:00:00',
    '{"address": "45 Rue du Faubourg...", "latitude": 48.8530, "longitude": 2.3726}',
    18.00,
    15,
    0,
    'DRAFT',
    '{"game_id": 2, "round_duration": 15, "num_rounds": 4}',
    NOW()
);

-- Association des langues
INSERT INTO events_event_languages (event_id, language_id)
VALUES (6, 3), (6, 1);  -- es, fr

-- Publication
UPDATE events_event
SET status = 'PUBLISHED',
    published_at = NOW()
WHERE id = 6;
```

#### Gestion des Participants et Annulation d'Événement

**Objectif** : Permettre à un administrateur de visualiser les participants et d'annuler un événement si nécessaire.

**Démonstration** :

1. **Visualisation des participants**
   - URL : `http://localhost:4200/fr/events/1` (en tant qu'organisateur)
   - Section spéciale "Gestion de l'événement" visible uniquement pour l'organisateur
   - Liste des participants confirmés :
     ```
     📊 Statistiques :
     - Places réservées : 8/20
     - Taux de remplissage : 40%
     - Revenus générés : 120,00 EUR

     👥 Liste des participants :
     1. Marie Dupont - marie.dupont@example.com
        Réservé le : 10/11/2025 | Payé : 15,00 EUR

     2. Jean Martin - jean.martin@example.com
        Réservé le : 11/11/2025 | Payé : 15,00 EUR

     3. Sarah Johnson - sarah.johnson@example.com
        Réservé le : 12/11/2025 | Payé : 15,00 EUR

     ... (5 autres participants)
     ```

2. **Modification de l'événement**
   - Bouton "Modifier l'événement" (si aucune réservation)
   - Si des réservations existent : modification limitée (description, prix NON modifiable)

3. **Annulation d'un événement**
   - Scénario : L'événement n'a pas assez de participants (< 5 personnes minimum)
   - Cliquer sur "Annuler l'événement"
   - Modal de confirmation :
     ```
     ⚠️ Annuler cet événement ?

     Cette action va :
     - Annuler toutes les réservations confirmées (8 réservations)
     - Rembourser automatiquement tous les participants (120,00 EUR)
     - Envoyer un email à tous les participants
     - Marquer l'événement comme CANCELLED

     Raison de l'annulation (optionnel) :
     [Pas assez de participants]

     [Annuler] [Confirmer l'annulation]
     ```

4. **Processus d'annulation automatique**
   - ✅ Statut de l'événement : PUBLISHED → CANCELLED
   - ✅ Remboursement automatique via Stripe pour toutes les 8 réservations
   - ✅ Statut des réservations : CONFIRMED → REFUNDED
   - ✅ Email envoyé automatiquement à tous les participants
   - ✅ Places libérées (8 → 0)
   - ✅ Message de confirmation : "L'événement a été annulé et tous les participants ont été remboursés."

**Code Backend - Annulation d'événement** : `backend/events/services/event_service.py`
```python
@staticmethod
@transaction.atomic
def cancel_event(event, reason=None):
    """Cancel an event and refund all bookings."""
    if event.status == Event.Status.CANCELLED:
        raise ValidationError("Event is already cancelled")

    if event.status == Event.Status.DRAFT:
        # Simple suppression si brouillon
        event.status = Event.Status.CANCELLED
        event.save()
        return event

    # Récupération de toutes les réservations confirmées
    confirmed_bookings = Booking.objects.filter(
        event=event,
        status=BookingStatus.CONFIRMED
    )

    refund_count = 0
    refund_errors = []

    # Remboursement de chaque réservation
    for booking in confirmed_bookings:
        try:
            # Remboursement via Stripe
            if booking.payment_intent_id:
                refund = stripe.Refund.create(
                    payment_intent=booking.payment_intent_id,
                    reason='requested_by_customer',
                    metadata={
                        'event_id': str(event.id),
                        'event_title': event.title,
                        'cancellation_reason': reason or 'Event cancelled'
                    }
                )
                booking.refund_id = refund['id']

            # Mise à jour du statut
            booking.status = BookingStatus.REFUNDED
            booking.cancelled_at = timezone.now()
            booking.save()

            # Email de notification
            send_booking_cancellation_email(booking, reason)

            refund_count += 1

        except Exception as e:
            logger.error(f"Failed to refund booking {booking.id}: {e}")
            refund_errors.append({
                'booking_id': booking.id,
                'user_email': booking.user.email,
                'error': str(e)
            })

    # Annulation de l'événement
    event.status = Event.Status.CANCELLED
    event.cancellation_reason = reason
    event.cancelled_at = timezone.now()
    event.current_participants = 0
    event.save()

    # Log d'audit
    AuditService.log_action(
        user=event.organizer,
        action='UPDATE',
        model_name='Event',
        object_id=event.id,
        changes={
            'status': {'old': 'PUBLISHED', 'new': 'CANCELLED'},
            'refunded_bookings': refund_count,
            'refund_errors': len(refund_errors),
            'reason': reason
        }
    )

    if refund_errors:
        logger.warning(f"Event {event.id} cancelled with {len(refund_errors)} refund errors")

    return event
```

**Base de données - Impact** :
```sql
-- Table: events_event
UPDATE events_event
SET status = 'CANCELLED',
    cancellation_reason = 'Pas assez de participants',
    cancelled_at = NOW(),
    current_participants = 0
WHERE id = 1;

-- Table: bookings_booking (toutes les réservations)
UPDATE bookings_booking
SET status = 'REFUNDED',
    cancelled_at = NOW()
WHERE event_id = 1 AND status = 'CONFIRMED';

-- Table: audit_auditlog
INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
VALUES (
    1,
    'UPDATE',
    'Event',
    1,
    '{"status": {"old": "PUBLISHED", "new": "CANCELLED"}, "refunded_bookings": 8, "reason": "Pas assez de participants"}',
    NOW()
);
```

---

## 2. Autres Fonctionnalités Pertinentes

### 2.1 Système de Paiement Stripe

**Objectif** : Intégration complète avec Stripe pour les paiements sécurisés et les remboursements automatiques.

**Fonctionnalités** :
- ✅ Création de Payment Intent pour chaque réservation
- ✅ Redirection vers Stripe Checkout (mode hosted)
- ✅ Gestion des webhooks pour confirmation automatique
- ✅ Remboursements automatiques en cas d'annulation
- ✅ Test en mode développement avec Stripe CLI
- ✅ Gestion des erreurs et retry automatique

**Configuration Stripe CLI** :

Pour tester les webhooks en local, Stripe CLI doit être configuré :

```bash
# Dans le terminal backend
cd backend

# Lancement du forwarding de webhooks
.\stripe.exe listen --forward-to http://localhost:8000/api/v1/payments/stripe-webhook/

# Résultat attendu :
> Ready! Your webhook signing secret is whsec_abcd1234... (^C to quit)
> Listening for events matching endpoint ID: we_abc123...
```

**Démonstration complète** :

1. **Création d'une réservation**
   - Membre réserve un événement
   - Payment Intent créé côté backend
   - Log Stripe CLI : `payment_intent.created [evt_abc123]`

2. **Paiement sur Stripe**
   - Utilisateur redirigé vers Stripe Checkout
   - Carte de test : `4242 4242 4242 4242`
   - Paiement effectué
   - Log Stripe CLI : `payment_intent.succeeded [evt_xyz789]`

3. **Webhook reçu**
   ```
   [2025-11-12 16:30:45] --> payment_intent.succeeded [evt_xyz789]
   POST http://localhost:8000/api/v1/payments/stripe-webhook/ [200]
   ```

4. **Confirmation automatique**
   - Réservation mise à jour : PENDING → CONFIRMED
   - Email envoyé au participant
   - Place décrémentée

5. **Annulation et remboursement**
   - Utilisateur annule sa réservation
   - Remboursement automatique déclenché
   - Log Stripe CLI :
     ```
     [2025-11-12 16:35:12] --> refund.created [evt_refund123]
     [2025-11-12 16:35:13] --> refund.succeeded [evt_refund456]
     ```
   - Réservation : CONFIRMED → CANCELLED
   - Email de confirmation d'annulation envoyé

**Code Backend - Création Payment Intent** : `backend/payments/services/payment_service.py`
```python
@staticmethod
def create_payment_intent(booking):
    """Create a Stripe Payment Intent for a booking."""
    try:
        # Création du Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=int(booking.amount * 100),  # Conversion en centimes
            currency='eur',
            metadata={
                'booking_id': str(booking.id),
                'user_id': str(booking.user.id),
                'user_email': booking.user.email,
                'event_id': str(booking.event.id),
                'event_title': booking.event.title
            },
            automatic_payment_methods={'enabled': True},
            description=f'Réservation pour {booking.event.title}'
        )

        # Sauvegarde de l'ID du Payment Intent
        booking.payment_intent_id = intent['id']
        booking.save()

        return intent['client_secret']

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise ValidationError(f"Payment error: {str(e)}")
```

**Code Backend - Remboursement** : `backend/payments/services/payment_service.py`
```python
@staticmethod
def create_refund(booking, reason='requested_by_customer'):
    """Create a refund for a booking."""
    if not booking.payment_intent_id:
        raise ValidationError("No payment intent found for this booking")

    try:
        refund = stripe.Refund.create(
            payment_intent=booking.payment_intent_id,
            reason=reason,
            metadata={
                'booking_id': str(booking.id),
                'event_id': str(booking.event.id),
                'event_title': booking.event.title
            }
        )

        booking.refund_id = refund['id']
        booking.save()

        return refund

    except stripe.error.StripeError as e:
        logger.error(f"Refund error: {e}")
        raise ValidationError(f"Refund error: {str(e)}")
```

**Variables d'environnement requises** :
```env
# backend/.env
STRIPE_PUBLISHABLE_KEY=pk_test_abc123...
STRIPE_SECRET_KEY=sk_test_xyz789...
STRIPE_WEBHOOK_SECRET=whsec_def456...
```

---

### 2.2 Gestion des Réservations

**Objectif** : Permettre aux membres de visualiser et gérer toutes leurs réservations avec différents statuts.

**Statuts des réservations** :
- 🟡 **PENDING** : En attente de paiement (Payment Intent créé)
- 🟢 **CONFIRMED** : Paiement confirmé, place réservée
- 🔴 **CANCELLED** : Annulée par l'utilisateur avant l'événement
- 🔵 **REFUNDED** : Remboursée suite à l'annulation de l'événement

**Démonstration** :

1. **Page "Mes Réservations"**
   - URL : `http://localhost:4200/fr/bookings`
   - Vue d'ensemble de toutes les réservations

2. **Filtres disponibles**
   ```
   Filtrer par statut :
   - ☑ Toutes (4)
   - ☐ Confirmées (2)
   - ☐ Annulées (1)
   - ☐ Remboursées (1)

   Trier par :
   - Date de l'événement (ascendant)
   - Date de réservation (descendant)
   - Prix (ascendant/descendant)
   ```

3. **Affichage d'une réservation confirmée**
   ```
   🎫 Réservation #1234 - ✅ CONFIRMÉE

   Événement : Échange linguistique Français-Anglais
   📅 Date : Vendredi 15 décembre 2025 à 19h00
   📍 Lieu : 123 Rue de la Paix, 75002 Paris
   💰 Montant payé : 15,00 EUR
   🆔 ID de paiement : pi_1ABC123...

   [Voir l'événement] [Annuler ma réservation]
   ```

4. **Actions disponibles selon le statut**
   - **CONFIRMED** : Voir l'événement, Annuler (si > 24h avant)
   - **CANCELLED** : Voir l'événement, Voir les détails du remboursement
   - **REFUNDED** : Voir l'événement (annulé), Voir le motif d'annulation
   - **PENDING** : Finaliser le paiement, Annuler

**Code Frontend** : `frontend/src/app/features/bookings/list/bookings-list.component.ts`
```typescript
export class BookingsListComponent implements OnInit {
  bookings = signal<Booking[]>([]);
  filteredBookings = signal<Booking[]>([]);
  selectedStatus = signal<BookingStatus | 'ALL'>('ALL');
  loading = signal(false);
  error = signal<string | null>(null);

  private readonly bookingsApi = inject(BookingsApiService);
  private readonly router = inject(Router);
  private readonly t = inject(TranslateService);

  ngOnInit() {
    this.loadBookings();
  }

  loadBookings() {
    this.loading.set(true);
    this.bookingsApi.getMyBookings()
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (bookings) => {
          this.bookings.set(bookings);
          this.filterBookings();
        },
        error: (err) => {
          this.error.set('BOOKINGS.ERROR_LOADING');
        }
      });
  }

  filterBookings() {
    const status = this.selectedStatus();
    const allBookings = this.bookings();

    if (status === 'ALL') {
      this.filteredBookings.set(allBookings);
    } else {
      this.filteredBookings.set(
        allBookings.filter(b => b.status === status)
      );
    }
  }

  cancelBooking(bookingId: number) {
    if (!confirm(this.t.instant('BOOKINGS.CONFIRM_CANCEL'))) {
      return;
    }

    this.bookingsApi.cancelBooking(bookingId)
      .subscribe({
        next: () => {
          // Mise à jour locale
          const bookings = this.bookings();
          const index = bookings.findIndex(b => b.id === bookingId);
          if (index !== -1) {
            bookings[index].status = 'CANCELLED';
            this.bookings.set([...bookings]);
            this.filterBookings();
          }
        },
        error: (err) => {
          alert(this.t.instant('BOOKINGS.ERROR_CANCEL'));
        }
      });
  }
}
```

---

### 2.3 Système d'Audit

**Objectif** : Tracer toutes les actions importantes pour la conformité RGPD, le débogage et l'analyse.

**Fonctionnalités** :
- ✅ Enregistrement automatique de toutes les modifications (CREATE, UPDATE, DELETE)
- ✅ Traçabilité complète : qui, quoi, quand, avant/après
- ✅ Filtrage par utilisateur, modèle, action, date
- ✅ Export des logs pour analyse (CSV, JSON)
- ✅ Conservation des logs même après suppression des utilisateurs

**Démonstration** :

1. **Accès aux logs d'audit** (admin uniquement)
   - URL : `http://localhost:4200/fr/admin/audit`
   - ⚠️ Accessible uniquement aux `is_staff=True`

2. **Filtres disponibles**
   ```
   Recherche avancée :
   - Utilisateur : [Tous] ▼
   - Modèle : [Tous] ▼ (User, Event, Booking, Payment)
   - Action : [Toutes] ▼ (CREATE, UPDATE, DELETE)
   - Date de début : [15/10/2025]
   - Date de fin : [15/11/2025]

   [Rechercher] [Exporter en CSV]
   ```

3. **Affichage des logs**
   ```
   📊 200 résultats trouvés

   Log #1234 - 12/11/2025 16:30:45
   👤 Utilisateur : marie.dupont@example.com (ID: 2)
   📝 Action : UPDATE
   📦 Modèle : Booking
   🆔 Object ID : 1
   🔄 Changements :
   {
     "status": {
       "old": "PENDING",
       "new": "CONFIRMED"
     },
     "payment_intent_id": "pi_1ABC123..."
   }
   🌐 IP : 192.168.1.100

   ---

   Log #1233 - 12/11/2025 16:30:40
   👤 Utilisateur : marie.dupont@example.com (ID: 2)
   📝 Action : CREATE
   📦 Modèle : Booking
   🆔 Object ID : 1
   🔄 Changements :
   {
     "event_id": 1,
     "amount": "15.00",
     "status": "PENDING"
   }
   🌐 IP : 192.168.1.100
   ```

4. **Export des logs**
   - Cliquer sur "Exporter en CSV"
   - Téléchargement d'un fichier : `audit_logs_2025-11-12.csv`
   - Contient tous les logs filtrés avec colonnes :
     ```
     timestamp,user_email,action,model_name,object_id,changes,ip_address
     ```

**Code Backend - Service d'Audit** : `backend/audit/services.py`
```python
class AuditService(BaseService):
    """Service for audit logging."""

    @staticmethod
    def log_action(user, action, model_name, object_id, changes=None, ip_address=None):
        """Create an audit log entry."""
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            changes=changes or {},
            ip_address=ip_address,
            timestamp=timezone.now()
        )

    @staticmethod
    def get_logs(user=None, model_name=None, action=None, start_date=None, end_date=None):
        """Get filtered audit logs."""
        queryset = AuditLog.objects.all()

        if user:
            queryset = queryset.filter(user=user)
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        if action:
            queryset = queryset.filter(action=action)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        return queryset.order_by('-timestamp')

    @staticmethod
    def export_logs_csv(queryset):
        """Export logs to CSV format."""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow([
            'Timestamp', 'User Email', 'Action', 'Model Name',
            'Object ID', 'Changes', 'IP Address'
        ])

        # Données
        for log in queryset:
            writer.writerow([
                log.timestamp.isoformat(),
                log.user.email if log.user else 'System',
                log.action,
                log.model_name,
                log.object_id,
                json.dumps(log.changes),
                log.ip_address or ''
            ])

        return output.getvalue()
```

**Base de données** :
```sql
-- Table: audit_auditlog
CREATE TABLE audit_auditlog (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users_user(id) ON DELETE SET NULL,
    action VARCHAR(10) NOT NULL,  -- CREATE, UPDATE, DELETE
    model_name VARCHAR(100) NOT NULL,
    object_id INTEGER NOT NULL,
    changes JSONB DEFAULT '{}',
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherches rapides
CREATE INDEX idx_audit_user ON audit_auditlog(user_id);
CREATE INDEX idx_audit_model ON audit_auditlog(model_name);
CREATE INDEX idx_audit_action ON audit_auditlog(action);
CREATE INDEX idx_audit_timestamp ON audit_auditlog(timestamp DESC);

-- Index composite pour filtres multiples
CREATE INDEX idx_audit_search ON audit_auditlog(user_id, model_name, action, timestamp DESC);
```

**Exemples de requêtes utiles** :
```sql
-- Toutes les réservations créées aujourd'hui
SELECT * FROM audit_auditlog
WHERE model_name = 'Booking'
  AND action = 'CREATE'
  AND timestamp >= CURRENT_DATE
ORDER BY timestamp DESC;

-- Toutes les actions d'un utilisateur spécifique
SELECT * FROM audit_auditlog
WHERE user_id = 2
ORDER BY timestamp DESC
LIMIT 50;

-- Tous les remboursements effectués
SELECT * FROM audit_auditlog
WHERE model_name = 'Booking'
  AND changes->>'status' LIKE '%REFUNDED%'
ORDER BY timestamp DESC;

-- Statistiques d'actions par jour
SELECT
    DATE(timestamp) as date,
    action,
    COUNT(*) as count
FROM audit_auditlog
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), action
ORDER BY date DESC, action;
```

---

### 2.4 Système de Jeux Collaboratifs

**Objectif** : Proposer des jeux interactifs pendant les événements pour favoriser l'apprentissage des langues de manière ludique et collaborative.

**Fonctionnalités** :
- ✅ 4 types de jeux disponibles (Description d'image, Association de mots, Débat, Jeu de rôle)
- ✅ Système de vote collaboratif (participants votent pour les meilleures réponses)
- ✅ Création de jeux uniquement par l'organisateur
- ✅ Vote uniquement pour les participants confirmés
- ✅ Détection automatique de la majorité et fin du jeu
- ✅ Gestion du timeout (fin automatique après temps imparti)
- ✅ Statistiques en temps réel (nombre de votes, répartition)
- ✅ 3 niveaux de difficulté (Facile, Moyen, Difficile)

**Types de jeux disponibles** :

1. **PICTURE_DESCRIPTION** : Description d'image
   - L'organisateur affiche une image
   - Les participants doivent décrire ce qu'ils voient
   - Vote pour la meilleure description

2. **WORD_ASSOCIATION** : Association de mots
   - L'organisateur propose un mot de départ
   - Les participants proposent des mots associés
   - Vote pour les associations les plus pertinentes

3. **DEBATE** : Débat
   - L'organisateur propose un sujet de débat
   - Les participants argumentent pour/contre
   - Vote pour les meilleurs arguments

4. **ROLE_PLAY** : Jeu de rôle
   - L'organisateur propose une situation
   - Les participants improvisent un dialogue
   - Vote pour la meilleure interprétation

---

#### Démonstration Point de Vue Administrateur (Création de Jeu)

**Prérequis** :
- Utilisateur connecté en tant qu'organisateur (Admin Conversa)
- Événement publié avec participants confirmés (événement #1)
- Navigateur : Chrome

**Étapes** :

1. **Accès à la page de l'événement**
   - URL : `http://localhost:4200/fr/events/1`
   - Section "Gestion de l'événement" visible pour l'organisateur
   - Bouton "Créer un jeu" disponible

2. **Création d'un nouveau jeu**
   ```
   Cliquer sur "Créer un jeu"

   Formulaire de création :
   ┌─────────────────────────────────────────────┐
   │ Créer un nouveau jeu                         │
   ├─────────────────────────────────────────────┤
   │ Type de jeu : [Description d'image] ▼        │
   │                                              │
   │ Difficulté : [○ Facile ⦿ Moyen ○ Difficile] │
   │                                              │
   │ Timeout (secondes) : [120]                   │
   │                                              │
   │ Question :                                   │
   │ ┌──────────────────────────────────────────┐ │
   │ │ Décrivez cette image de la Tour Eiffel   │ │
   │ │ en utilisant au moins 5 adjectifs.       │ │
   │ └──────────────────────────────────────────┘ │
   │                                              │
   │ [Annuler]                    [Créer le jeu]  │
   └─────────────────────────────────────────────┘
   ```

3. **Soumission du formulaire**
   - Cliquer sur "Créer le jeu"
   - ✅ Requête POST vers `/api/v1/games/create/`
   - ✅ Validation : seul l'organisateur peut créer un jeu
   - ✅ Validation : au moins 2 participants confirmés requis
   - ✅ Création du jeu avec statut ACTIVE
   - ✅ Message de confirmation : "Le jeu a été créé avec succès !"

4. **Affichage du jeu actif**
   ```
   🎮 Jeu en cours : Description d'image (Moyen)

   Question : Décrivez cette image de la Tour Eiffel en utilisant
              au moins 5 adjectifs.

   ⏱️ Temps restant : 01:58

   📊 Statistiques en direct :
   - Participants totaux : 8
   - Votes enregistrés : 0/8
   - Réponses soumises : 0

   ⚠️ En attente des réponses des participants...
   ```

**Code Backend - Création du jeu** : `backend/games/services/game_service.py`
```python
@staticmethod
@transaction.atomic
def create_game(event, game_type, difficulty, timeout, question):
    """Create a new game for an event.

    Only the event organizer can create games.
    At least 2 confirmed participants are required.
    """
    # Vérifier qu'il n'y a pas déjà un jeu actif
    active_game = Game.objects.filter(
        event=event,
        status=GameStatus.ACTIVE
    ).first()

    if active_game:
        raise ValidationError("An active game already exists for this event")

    # Vérifier le nombre de participants confirmés
    confirmed_count = Booking.objects.filter(
        event=event,
        status=BookingStatus.CONFIRMED
    ).count()

    if confirmed_count < 2:
        raise ValidationError("At least 2 confirmed participants required")

    # Créer le jeu
    game = Game.objects.create(
        event=event,
        game_type=game_type,
        difficulty=difficulty,
        timeout=timeout,
        question=question,
        status=GameStatus.ACTIVE,
        created_at=timezone.now()
    )

    # Log d'audit
    AuditService.log_action(
        user=event.organizer,
        action='CREATE',
        model_name='Game',
        object_id=game.id,
        changes={
            'event_id': event.id,
            'game_type': game_type,
            'difficulty': difficulty,
            'timeout': timeout,
            'question': question
        }
    )

    return game
```

**Base de données - Impact** :
```sql
-- Table: games_game
INSERT INTO games_game (
    event_id,
    game_type,
    difficulty,
    timeout,
    question,
    status,
    created_at,
    expires_at
) VALUES (
    1,
    'PICTURE_DESCRIPTION',
    'MEDIUM',
    120,
    'Décrivez cette image de la Tour Eiffel en utilisant au moins 5 adjectifs.',
    'ACTIVE',
    NOW(),
    NOW() + INTERVAL 120 SECOND
);

-- Table: audit_auditlog
INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
VALUES (
    1,  -- Admin Conversa (organisateur)
    'CREATE',
    'Game',
    1,
    '{"event_id": 1, "game_type": "PICTURE_DESCRIPTION", "difficulty": "MEDIUM", "timeout": 120}',
    NOW()
);
```

---

#### Démonstration Point de Vue Participant (Vote)

**Prérequis** :
- Utilisateur connecté en tant que participant (Marie Dupont)
- Réservation confirmée pour l'événement #1
- Jeu actif créé par l'organisateur
- Navigateur : Firefox (pour différencier du navigateur admin)

**Étapes** :

1. **Accès à la page de l'événement**
   - URL : `http://localhost:4200/fr/events/1`
   - Section "Jeu en cours" visible pour les participants confirmés

2. **Affichage du jeu actif**
   ```
   🎮 Jeu en cours : Description d'image (Moyen)

   Question : Décrivez cette image de la Tour Eiffel en utilisant
              au moins 5 adjectifs.

   ⏱️ Temps restant : 01:45

   Votre réponse :
   ┌─────────────────────────────────────────────────────┐
   │ [Saisissez votre réponse ici...]                    │
   │                                                      │
   │                                                      │
   └─────────────────────────────────────────────────────┘

   [Soumettre ma réponse]
   ```

3. **Soumission de la réponse**
   - Participant Marie saisit : "Majestueuse, imposante, métallique, illuminée, emblématique"
   - Cliquer sur "Soumettre ma réponse"
   - ✅ Requête POST vers `/api/v1/games/1/vote/`
   - ✅ Validation : participant confirmé uniquement
   - ✅ Validation : un seul vote par participant
   - ✅ Vote enregistré avec la réponse

4. **Confirmation du vote**
   ```
   ✅ Votre réponse a été enregistrée !

   Votre réponse : "Majestueuse, imposante, métallique, illuminée, emblématique"

   📊 Votes actuels : 1/8 participants ont voté

   ⏱️ En attente des autres participants...
   ```

5. **Après que tous les participants ont voté**
   ```
   🎉 Le jeu est terminé !

   📊 Résultats finaux :

   🥇 Réponse gagnante (5 votes) :
   "Majestueuse, imposante, métallique, illuminée, emblématique"
   - Votée par : Marie D., Jean P., Sophie M., Luc B., Emma R.

   🥈 Deuxième place (2 votes) :
   "Grande, historique, parisienne, touristique, iconique"
   - Votée par : Pierre L., Claire D.

   🥉 Troisième place (1 vote) :
   "Haute, métallique, française, célèbre, impressionnante"
   - Votée par : Marc T.

   ✨ Statut : COMPLETED
   ```

**Code Backend - Vote** : `backend/games/services/game_service.py`
```python
@staticmethod
@transaction.atomic
def submit_vote(game, user, answer):
    """Submit a vote for a game.

    Only confirmed participants can vote.
    One vote per participant.
    Automatically completes game when majority is reached.
    """
    # Vérifier que le jeu est actif
    if game.status != GameStatus.ACTIVE:
        raise ValidationError("This game is no longer active")

    # Vérifier que le timeout n'est pas dépassé
    if timezone.now() > game.expires_at:
        game.status = GameStatus.TIMEOUT
        game.save()
        raise ValidationError("Game timeout has expired")

    # Vérifier que l'utilisateur a une réservation confirmée
    booking = Booking.objects.filter(
        event=game.event,
        user=user,
        status=BookingStatus.CONFIRMED
    ).first()

    if not booking:
        raise ValidationError("Only confirmed participants can vote")

    # Vérifier que l'utilisateur n'a pas déjà voté
    if GameVote.objects.filter(game=game, user=user).exists():
        raise ValidationError("You have already voted for this game")

    # Enregistrer le vote
    vote = GameVote.objects.create(
        game=game,
        user=user,
        answer=answer,
        voted_at=timezone.now()
    )

    # Vérifier si la majorité a voté
    total_participants = Booking.objects.filter(
        event=game.event,
        status=BookingStatus.CONFIRMED
    ).count()

    votes_count = GameVote.objects.filter(game=game).count()

    # Majorité atteinte (> 50%)
    if votes_count > (total_participants / 2):
        game.status = GameStatus.COMPLETED
        game.completed_at = timezone.now()
        game.save()

    # Log d'audit
    AuditService.log_action(
        user=user,
        action='CREATE',
        model_name='GameVote',
        object_id=vote.id,
        changes={
            'game_id': game.id,
            'answer': answer,
            'votes_count': votes_count,
            'total_participants': total_participants
        }
    )

    return vote, game.status
```

**Code Frontend - Interface de vote** : `frontend/src/app/features/games/vote/game-vote.component.ts`
```typescript
export class GameVoteComponent implements OnInit {
  game = signal<Game | null>(null);
  myVote = signal<GameVote | null>(null);
  stats = signal<GameStats | null>(null);
  answerForm: FormGroup;
  loading = signal(false);
  error = signal<string | null>(null);
  timeRemaining = signal<number>(0);

  private readonly gamesApi = inject(GamesApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private timerInterval?: any;

  constructor() {
    this.answerForm = this.fb.group({
      answer: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(500)]]
    });
  }

  ngOnInit() {
    const eventId = this.route.snapshot.params['id'];
    this.loadActiveGame(eventId);
    this.startTimer();
  }

  loadActiveGame(eventId: number) {
    this.gamesApi.getActiveGame(eventId)
      .subscribe({
        next: (game) => {
          this.game.set(game);
          this.loadStats();
          this.checkIfAlreadyVoted();
        },
        error: () => this.error.set('GAMES.ERROR_LOADING')
      });
  }

  loadStats() {
    const game = this.game();
    if (!game) return;

    this.gamesApi.getGameStats(game.id)
      .subscribe({
        next: (stats) => this.stats.set(stats),
        error: () => console.error('Error loading stats')
      });
  }

  checkIfAlreadyVoted() {
    const game = this.game();
    if (!game) return;

    // Vérifier si l'utilisateur a déjà voté
    const currentUserId = this.authService.getCurrentUserId();
    const myVote = game.votes?.find(v => v.user_id === currentUserId);
    this.myVote.set(myVote || null);
  }

  submitVote() {
    if (this.answerForm.invalid || this.loading()) return;

    const game = this.game();
    if (!game) return;

    this.loading.set(true);
    this.error.set(null);

    const answer = this.answerForm.value.answer;

    this.gamesApi.submitVote(game.id, answer)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (vote) => {
          this.myVote.set(vote);
          this.loadStats();
          // Recharger le jeu pour voir si statut a changé
          this.loadActiveGame(game.event_id);
        },
        error: (err) => {
          if (err.status === 400) {
            this.error.set('GAMES.ERROR_ALREADY_VOTED');
          } else {
            this.error.set('GAMES.ERROR_SUBMIT');
          }
        }
      });
  }

  startTimer() {
    this.timerInterval = setInterval(() => {
      const game = this.game();
      if (!game || !game.expires_at) return;

      const now = Date.now();
      const expiresAt = new Date(game.expires_at).getTime();
      const remaining = Math.max(0, Math.floor((expiresAt - now) / 1000));

      this.timeRemaining.set(remaining);

      if (remaining === 0) {
        clearInterval(this.timerInterval);
        this.loadActiveGame(game.event_id); // Recharger pour voir statut TIMEOUT
      }
    }, 1000);
  }

  ngOnDestroy() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }
}
```

**Base de données - Impact après votes** :
```sql
-- Table: games_gamevote (8 votes des participants)
INSERT INTO games_gamevote (game_id, user_id, answer, voted_at) VALUES
(1, 2, 'Majestueuse, imposante, métallique, illuminée, emblématique', '2025-11-12 16:35:00'),
(1, 3, 'Majestueuse, imposante, métallique, illuminée, emblématique', '2025-11-12 16:35:10'),
(1, 4, 'Grande, historique, parisienne, touristique, iconique', '2025-11-12 16:35:15'),
(1, 5, 'Majestueuse, imposante, métallique, illuminée, emblématique', '2025-11-12 16:35:20'),
(1, 6, 'Haute, métallique, française, célèbre, impressionnante', '2025-11-12 16:35:25'),
(1, 7, 'Grande, historique, parisienne, touristique, iconique', '2025-11-12 16:35:30'),
(1, 8, 'Majestueuse, imposante, métallique, illuminée, emblématique', '2025-11-12 16:35:35'),
(1, 9, 'Majestueuse, imposante, métallique, illuminée, emblématique', '2025-11-12 16:35:40');

-- Table: games_game (mise à jour du statut après majorité)
UPDATE games_game
SET status = 'COMPLETED',
    completed_at = '2025-11-12 16:35:40'
WHERE id = 1;

-- Table: audit_auditlog (log pour chaque vote)
INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp) VALUES
(2, 'CREATE', 'GameVote', 1, '{"game_id": 1, "votes_count": 1, "total_participants": 8}', '2025-11-12 16:35:00'),
(3, 'CREATE', 'GameVote', 2, '{"game_id": 1, "votes_count": 2, "total_participants": 8}', '2025-11-12 16:35:10'),
-- ... (6 autres logs similaires)
(9, 'CREATE', 'GameVote', 8, '{"game_id": 1, "votes_count": 8, "total_participants": 8}', '2025-11-12 16:35:40');
```

---

#### Statistiques en Temps Réel

**Endpoint** : `GET /api/v1/games/{id}/stats/`

**Réponse** :
```json
{
  "game_id": 1,
  "total_votes": 8,
  "total_participants": 8,
  "participation_rate": 100.0,
  "status": "COMPLETED",
  "time_remaining": 0,
  "answers_distribution": {
    "Majestueuse, imposante, métallique, illuminée, emblématique": {
      "count": 5,
      "percentage": 62.5,
      "voters": ["marie.dupont@example.com", "jean.petit@example.com", ...]
    },
    "Grande, historique, parisienne, touristique, iconique": {
      "count": 2,
      "percentage": 25.0,
      "voters": ["pierre.louis@example.com", "claire.durand@example.com"]
    },
    "Haute, métallique, française, célèbre, impressionnante": {
      "count": 1,
      "percentage": 12.5,
      "voters": ["marc.thomas@example.com"]
    }
  },
  "winning_answer": "Majestueuse, imposante, métallique, illuminée, emblématique",
  "winning_votes": 5
}
```

**Code Backend - Statistiques** : `backend/games/services/game_service.py`
```python
@staticmethod
def get_game_statistics(game):
    """Get real-time statistics for a game."""
    from collections import Counter

    votes = GameVote.objects.filter(game=game).select_related('user')
    total_participants = Booking.objects.filter(
        event=game.event,
        status=BookingStatus.CONFIRMED
    ).count()

    # Compter les réponses
    answers = [vote.answer for vote in votes]
    answer_counts = Counter(answers)

    # Distribution des réponses
    distribution = {}
    for answer, count in answer_counts.items():
        voters = [
            vote.user.email
            for vote in votes
            if vote.answer == answer
        ]
        distribution[answer] = {
            'count': count,
            'percentage': round((count / len(votes)) * 100, 2) if votes else 0,
            'voters': voters
        }

    # Réponse gagnante
    winning_answer = answer_counts.most_common(1)[0] if answer_counts else None

    # Temps restant
    time_remaining = 0
    if game.status == GameStatus.ACTIVE and game.expires_at:
        time_remaining = max(0, (game.expires_at - timezone.now()).total_seconds())

    return {
        'game_id': game.id,
        'total_votes': len(votes),
        'total_participants': total_participants,
        'participation_rate': round((len(votes) / total_participants) * 100, 2) if total_participants else 0,
        'status': game.status,
        'time_remaining': int(time_remaining),
        'answers_distribution': distribution,
        'winning_answer': winning_answer[0] if winning_answer else None,
        'winning_votes': winning_answer[1] if winning_answer else 0
    }
```

---

#### Gestion du Timeout

**Comportement automatique** :
- ✅ Tâche Celery vérifie les jeux expirés toutes les 30 secondes
- ✅ Jeux actifs dépassant `expires_at` → statut TIMEOUT
- ✅ Frontend affiche message "Temps écoulé !"
- ✅ Résultats partiels affichés (votes enregistrés avant timeout)

**Code Backend - Tâche Celery** : `backend/games/tasks.py`
```python
from celery import shared_task
from django.utils import timezone
from .models import Game, GameStatus

@shared_task
def check_game_timeouts():
    """Check for expired games and mark them as timeout."""
    expired_games = Game.objects.filter(
        status=GameStatus.ACTIVE,
        expires_at__lt=timezone.now()
    )

    count = 0
    for game in expired_games:
        game.status = GameStatus.TIMEOUT
        game.completed_at = timezone.now()
        game.save()
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

**Configuration Celery Beat** : `backend/config/celery.py`
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-game-timeouts': {
        'task': 'games.tasks.check_game_timeouts',
        'schedule': 30.0,  # Every 30 seconds
    },
}
```

---

## 3. Multilinguisme

**Objectif** : Support complet de 3 langues (Français, Anglais, Néerlandais) pour tous les utilisateurs.

### 3.1 Démonstration du changement de langue

**Méthode 1 : Sélecteur de langue dans le header**

1. **Langue actuelle : Français**
   - URL : `http://localhost:4200/fr/events`
   - Cliquer sur le sélecteur de langue (icône 🌐 avec "FR")

2. **Menu déroulant**
   ```
   Choisir la langue :
   ✓ 🇫🇷 Français
     🇬🇧 English
     🇳🇱 Nederlands
   ```

3. **Changement vers l'anglais**
   - Cliquer sur "🇬🇧 English"
   - ✅ Redirection instantanée : `http://localhost:4200/en/events`
   - ✅ Tous les textes traduits immédiatement :
     ```
     Avant (FR) :
     - "Événements linguistiques"
     - "Réserver ma place"
     - "Places disponibles"

     Après (EN) :
     - "Language Events"
     - "Book my spot"
     - "Available seats"
     ```
   - ✅ Langue sauvegardée dans localStorage
   - ✅ Sélection conservée pour la session

4. **Changement vers le néerlandais**
   - Cliquer sur "🇳🇱 Nederlands"
   - ✅ Redirection : `http://localhost:4200/nl/events`
   - ✅ Interface complète en néerlandais :
     ```
     - "Taalevenementen"
     - "Reserveer mijn plek"
     - "Beschikbare plaatsen"
     ```

**Méthode 2 : URL directe**

Toutes les routes sont disponibles dans les 3 langues :
```
Français :   http://localhost:4200/fr/events
             http://localhost:4200/fr/events/1
             http://localhost:4200/fr/bookings

Anglais :    http://localhost:4200/en/events
             http://localhost:4200/en/events/1
             http://localhost:4200/en/bookings

Néerlandais: http://localhost:4200/nl/events
             http://localhost:4200/nl/events/1
             http://localhost:4200/nl/bookings
```

**Méthode 3 : Préférence navigateur**

Si l'utilisateur accède à l'URL racine sans langue spécifiée, le système détecte automatiquement la langue du navigateur :
```
Navigateur en français → http://localhost:4200/ → redirection vers /fr/events
Navigateur en anglais → http://localhost:4200/ → redirection vers /en/events
Autre langue → http://localhost:4200/ → redirection vers /fr/events (défaut)
```

---

### 3.2 Architecture du système i18n

**Structure des fichiers de traduction** :

```
frontend/src/assets/i18n/
├── fr.json  (Français - 2500+ clés)
├── en.json  (English - 2500+ clés)
└── nl.json  (Nederlands - 2500+ clés)
```

**Exemple de traductions complètes** : `frontend/src/assets/i18n/fr.json`
```json
{
  "common": {
    "brand": "Conversa",
    "save": "Enregistrer",
    "cancel": "Annuler",
    "back": "Retour",
    "loading": "Chargement..."
  },
  "nav": {
    "events": "Événements",
    "my_bookings": "Mes réservations"
  },
  "events": {
    "title": "Événements linguistiques",
    "create": "Créer un événement",
    "details": "Détails de l'événement",
    "book_now": "Réserver ma place",
    "price": "Prix",
    "participants": "Participants",
    "available_seats": "{{count}} places disponibles",
    "date": "Date",
    "location": "Lieu",
    "organizer": "Organisateur",
    "status": {
      "draft": "Brouillon",
      "published": "Publié",
      "cancelled": "Annulé"
    }
  },
  "bookings": {
    "my_bookings": "Mes réservations",
    "status": {
      "pending": "En attente",
      "confirmed": "Confirmée",
      "cancelled": "Annulée",
      "refunded": "Remboursée"
    },
    "cancel_booking": "Annuler ma réservation",
    "confirm_cancel": "Êtes-vous sûr de vouloir annuler cette réservation ?",
    "cancelled_success": "Votre réservation a été annulée avec succès."
  }
}
```

**Même structure en anglais** : `frontend/src/assets/i18n/en.json`
```json
{
  "common": {
    "brand": "Conversa",
    "save": "Save",
    "cancel": "Cancel",
    "back": "Back",
    "loading": "Loading..."
  },
  "nav": {
    "events": "Events",
    "my_bookings": "My bookings"
  },
  "events": {
    "title": "Language Events",
    "create": "Create an event",
    "details": "Event details",
    "book_now": "Book my spot",
    "price": "Price",
    "participants": "Participants",
    "available_seats": "{{count}} seats available",
    "date": "Date",
    "location": "Location",
    "organizer": "Organizer",
    "status": {
      "draft": "Draft",
      "published": "Published",
      "cancelled": "Cancelled"
    }
  },
  "bookings": {
    "my_bookings": "My bookings",
    "status": {
      "pending": "Pending",
      "confirmed": "Confirmed",
      "cancelled": "Cancelled",
      "refunded": "Refunded"
    },
    "cancel_booking": "Cancel my booking",
    "confirm_cancel": "Are you sure you want to cancel this booking?",
    "cancelled_success": "Your booking has been cancelled successfully."
  }
}
```

---

### 3.3 Utilisation dans les templates

**Template Angular avec le pipe `t`** :

```html
<!-- frontend/src/app/features/events/list/events-list.component.html -->
<shared-container>
  <div class="events-header">
    <h1 class="title">{{ 'events.title' | t }}</h1>

    @if (isStaff) {
      <shared-button (click)="createEvent()">
        {{ 'events.create' | t }}
      </shared-button>
    }
  </div>

  <div class="events-grid">
    @for (event of events(); track event.id) {
      <shared-card class="event-card">
        <h2>{{ event.title }}</h2>

        <div class="event-info">
          <p>📅 {{ 'events.date' | t }}: {{ event.date | date:'short' }}</p>
          <p>📍 {{ 'events.location' | t }}: {{ event.location.address }}</p>
          <p>💰 {{ 'events.price' | t }}: {{ event.price | currency:'EUR' }}</p>
          <p>👥 {{ 'events.available_seats' | t: {count: event.available_seats} }}</p>
        </div>

        <shared-button variant="primary" [routerLink]="['/', lang, 'events', event.id]">
          {{ 'events.book_now' | t }}
        </shared-button>
      </shared-card>
    }
  </div>
</shared-container>
```

**Résultat rendu selon la langue** :

```
Français (FR) :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Événements linguistiques
[Créer un événement]

┌─────────────────────────────────┐
│ Échange linguistique FR-EN      │
│                                 │
│ 📅 Date : 15/12/2025 19:00     │
│ 📍 Lieu : 123 Rue de la Paix   │
│ 💰 Prix : 15,00 €              │
│ 👥 12 places disponibles        │
│                                 │
│     [Réserver ma place]         │
└─────────────────────────────────┘

Anglais (EN) :
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language Events
[Create an event]

┌─────────────────────────────────┐
│ Échange linguistique FR-EN      │
│                                 │
│ 📅 Date: 12/15/2025 7:00 PM    │
│ 📍 Location: 123 Rue de la Paix│
│ 💰 Price: €15.00               │
│ 👥 12 seats available           │
│                                 │
│     [Book my spot]              │
└─────────────────────────────────┘
```

---

### 3.4 Service de traduction

**Pipe personnalisé** : `frontend/src/app/core/i18n/t.pipe.ts`
```typescript
@Pipe({
  name: 't',
  standalone: true,
  pure: false
})
export class TPipe implements PipeTransform {
  private translations: any = {};
  private currentLang: string = 'fr';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.detectLanguage();
    this.loadTranslations();
  }

  transform(key: string, params?: any): string {
    // Récupération de la traduction
    const translation = this.getNestedTranslation(key);

    // Interpolation des paramètres
    if (params && translation) {
      return this.interpolate(translation, params);
    }

    return translation || key;
  }

  private getNestedTranslation(key: string): string {
    const keys = key.split('.');
    let result = this.translations;

    for (const k of keys) {
      result = result?.[k];
    }

    return result;
  }

  private interpolate(template: string, params: any): string {
    return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
      return params[key] !== undefined ? params[key] : match;
    });
  }

  private detectLanguage() {
    // Détection depuis l'URL
    const urlSegments = this.router.url.split('/');
    const langFromUrl = urlSegments[1];

    if (['fr', 'en', 'nl'].includes(langFromUrl)) {
      this.currentLang = langFromUrl;
    } else {
      // Détection depuis le navigateur
      const browserLang = navigator.language.split('-')[0];
      this.currentLang = ['fr', 'en', 'nl'].includes(browserLang) ? browserLang : 'fr';
    }
  }

  private loadTranslations() {
    this.http
      .get(`/assets/i18n/${this.currentLang}.json`)
      .subscribe((translations) => {
        this.translations = translations;
      });
  }
}
```

---

### 3.5 Backend - Support multilingue des emails

Le backend envoie également des emails dans la langue de l'utilisateur :

**Service d'email** : `backend/common/services/email_service.py`
```python
class EmailService:
    """Service for sending multilingual emails."""

    @staticmethod
    def send_booking_confirmation_email(booking, language='fr'):
        """Send booking confirmation email in user's preferred language."""
        templates = {
            'fr': 'emails/booking_confirmation_fr.html',
            'en': 'emails/booking_confirmation_en.html',
            'nl': 'emails/booking_confirmation_nl.html'
        }

        subjects = {
            'fr': "Confirmation de réservation - {}",
            'en': "Booking confirmation - {}",
            'nl': "Reserveringsbevestiging - {}"
        }

        template = templates.get(language, templates['fr'])
        subject = subjects.get(language, subjects['fr'])

        context = {
            'user': booking.user,
            'event': booking.event,
            'booking': booking,
            'language': language
        }

        send_mail(
            subject=subject.format(booking.event.title),
            message=render_to_string(template, context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            html_message=render_to_string(template, context)
        )
```

**Template email FR** : `backend/templates/emails/booking_confirmation_fr.html`
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h1>Bonjour {{ user.first_name }},</h1>

    <p>Votre réservation a été confirmée avec succès !</p>

    <h2>Détails de l'événement :</h2>
    <ul>
        <li><strong>Événement :</strong> {{ event.title }}</li>
        <li><strong>Date :</strong> {{ event.date|date:"d/m/Y à H:i" }}</li>
        <li><strong>Lieu :</strong> {{ event.location.address }}</li>
        <li><strong>Prix :</strong> {{ booking.amount }} EUR</li>
    </ul>

    <p>Nous avons hâte de vous voir !</p>

    <p>Cordialement,<br>L'équipe Conversa</p>
</body>
</html>
```

---

## 4. Démonstration API

### 4.1 Endpoints GET

#### GET `/api/v1/events/` - Liste des événements

**Description** : Récupère la liste de tous les événements publiés avec pagination et filtres.

**Démonstration avec Postman** :

1. **Configuration de la requête**
   ```
   Method: GET
   URL: http://localhost:8000/api/v1/events/
   Headers:
     Content-Type: application/json
   ```

2. **Envoi de la requête**
   - Cliquer sur "Send" dans Postman

3. **Réponse attendue** (Status: 200 OK)
   ```json
   {
     "count": 5,
     "next": null,
     "previous": null,
     "results": [
       {
         "id": 1,
         "title": "Échange linguistique Français-Anglais",
         "description": "Rencontre conviviale pour pratiquer le français et l'anglais dans une ambiance détendue.",
         "date": "2025-12-15T19:00:00Z",
         "location": {
           "address": "123 Rue de la Paix, 75002 Paris, France",
           "latitude": 48.8698,
           "longitude": 2.3314
         },
         "price": "15.00",
         "max_participants": 20,
         "current_participants": 8,
         "available_seats": 12,
         "status": "PUBLISHED",
         "organizer": {
           "id": 1,
           "first_name": "Admin",
           "last_name": "Conversa",
           "email": "admin@conversa.com"
         },
         "languages": [
           {
             "code": "fr",
             "name": "Français"
           },
           {
             "code": "en",
             "name": "English"
           }
         ],
         "game_config": {
           "game_id": 1,
           "game_name": "Speed Meeting",
           "round_duration": 10,
           "num_rounds": 6
         },
         "published_at": "2025-11-01T10:00:00Z",
         "created_at": "2025-10-30T14:30:00Z"
       },
       {
         "id": 6,
         "title": "Soirée Espagnol-Français",
         "description": "Venez pratiquer l'espagnol dans une ambiance conviviale autour de tapas et de sangria.",
         "date": "2025-12-20T20:00:00Z",
         "location": {
           "address": "45 Rue du Faubourg Saint-Antoine, 75011 Paris, France",
           "latitude": 48.8530,
           "longitude": 2.3726
         },
         "price": "18.00",
         "max_participants": 15,
         "current_participants": 0,
         "available_seats": 15,
         "status": "PUBLISHED",
         "organizer": {
           "id": 1,
           "first_name": "Admin",
           "last_name": "Conversa"
         },
         "languages": [
           {
             "code": "es",
             "name": "Español"
           },
           {
             "code": "fr",
             "name": "Français"
           }
         ],
         "game_config": {
           "game_id": 2,
           "game_name": "Conversation en Rond",
           "round_duration": 15,
           "num_rounds": 4
         },
         "published_at": "2025-11-12T15:35:00Z",
         "created_at": "2025-11-12T15:30:00Z"
       }
     ]
   }
   ```

4. **Filtres disponibles**
   ```
   GET /api/v1/events/?status=PUBLISHED
   GET /api/v1/events/?date__gte=2025-12-01
   GET /api/v1/events/?date__lte=2025-12-31
   GET /api/v1/events/?languages=fr,en
   GET /api/v1/events/?price__lte=20
   GET /api/v1/events/?max_participants__gte=10
   GET /api/v1/events/?search=espagnol
   ```

**Code Backend** : `backend/events/views.py`
```python
class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for Event CRUD operations."""
    queryset = Event.objects.filter(status=Event.Status.PUBLISHED)
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['status', 'organizer', 'languages']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'price', 'created_at']
    ordering = ['date']

    def get_queryset(self):
        """Filter events based on query parameters."""
        queryset = super().get_queryset()

        # Filtrage par date
        date_gte = self.request.query_params.get('date__gte')
        if date_gte:
            queryset = queryset.filter(date__gte=date_gte)

        date_lte = self.request.query_params.get('date__lte')
        if date_lte:
            queryset = queryset.filter(date__lte=date_lte)

        # Filtrage par prix
        price_lte = self.request.query_params.get('price__lte')
        if price_lte:
            queryset = queryset.filter(price__lte=price_lte)

        return queryset
```

---

#### GET `/api/v1/bookings/my-bookings/` - Mes réservations

**Description** : Récupère toutes les réservations de l'utilisateur authentifié.

**Démonstration avec Postman** :

1. **Configuration de la requête**
   ```
   Method: GET
   URL: http://localhost:8000/api/v1/bookings/my-bookings/
   Headers:
     Content-Type: application/json
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

   ⚠️ **Important** : Le token JWT est requis

2. **Réponse attendue** (Status: 200 OK)
   ```json
   [
     {
       "id": 1,
       "event": {
         "id": 1,
         "title": "Échange linguistique Français-Anglais",
         "date": "2025-12-15T19:00:00Z",
         "location": {
           "address": "123 Rue de la Paix, 75002 Paris"
         },
         "price": "15.00"
       },
       "status": "CONFIRMED",
       "amount": "15.00",
       "payment_intent_id": "pi_1ABC123xyz",
       "created_at": "2025-11-10T14:30:00Z",
       "confirmed_at": "2025-11-10T14:31:00Z"
     },
     {
       "id": 2,
       "event": {
         "id": 3,
         "title": "Conversation Espagnol débutants",
         "date": "2025-11-20T18:30:00Z",
         "location": {
           "address": "78 Avenue des Champs-Élysées, 75008 Paris"
         },
         "price": "12.00"
       },
       "status": "CANCELLED",
       "amount": "12.00",
       "payment_intent_id": "pi_1DEF456abc",
       "refund_id": "re_1GHI789def",
       "created_at": "2025-11-05T10:00:00Z",
       "cancelled_at": "2025-11-08T16:20:00Z"
     }
   ]
   ```

**Code Backend** : `backend/bookings/views.py`
```python
class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for Booking operations."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only bookings for the current user."""
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get all bookings for current user."""
        bookings = self.get_queryset()
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
```

---

### 4.2 Endpoints POST/PUT/DELETE

#### POST `/api/v1/events/` - Création d'un événement

**Description** : Créer un nouvel événement (réservé aux staff).

**Démonstration avec Postman** :

1. **Configuration de la requête**
   ```
   Method: POST
   URL: http://localhost:8000/api/v1/events/
   Headers:
     Content-Type: application/json
     Authorization: Bearer <admin_token>
   ```

2. **Body (JSON)** :
   ```json
   {
     "title": "Atelier Allemand intensif",
     "description": "Session intensive de conversation allemande pour niveau intermédiaire. Travail sur la grammaire et le vocabulaire du quotidien.",
     "date": "2025-12-25T14:00:00Z",
     "location": {
       "address": "89 Boulevard de Sébastopol, 75002 Paris, France",
       "latitude": 48.8644,
       "longitude": 2.3518
     },
     "price": "25.00",
     "max_participants": 10,
     "languages": ["de", "fr"],
     "game_config": {
       "game_id": 3,
       "round_duration": 20,
       "num_rounds": 3
     }
   }
   ```

3. **Réponse attendue** (Status: 201 Created)
   ```json
   {
     "id": 7,
     "title": "Atelier Allemand intensif",
     "description": "Session intensive de conversation allemande...",
     "date": "2025-12-25T14:00:00Z",
     "location": {
       "address": "89 Boulevard de Sébastopol, 75002 Paris, France",
       "latitude": 48.8644,
       "longitude": 2.3518
     },
     "price": "25.00",
     "max_participants": 10,
     "current_participants": 0,
     "available_seats": 10,
     "status": "DRAFT",
     "organizer": {
       "id": 1,
       "first_name": "Admin",
       "last_name": "Conversa"
     },
     "languages": [
       {
         "code": "de",
         "name": "Deutsch"
       },
       {
         "code": "fr",
         "name": "Français"
       }
     ],
     "game_config": {
       "game_id": 3,
       "round_duration": 20,
       "num_rounds": 3
     },
     "created_at": "2025-11-12T16:45:00Z"
   }
   ```

4. **Réponse en cas d'erreur** (Status: 403 Forbidden)
   ```json
   {
     "detail": "Only staff members can create events"
   }
   ```

5. **Base de données - Impact** :
   ```sql
   -- Table: events_event
   INSERT INTO events_event (
     organizer_id, title, description, date, location,
     price, max_participants, current_participants,
     status, game_config, created_at
   )
   VALUES (
     1,
     'Atelier Allemand intensif',
     'Session intensive de conversation allemande...',
     '2025-12-25 14:00:00',
     '{"address": "89 Boulevard...", "latitude": 48.8644, "longitude": 2.3518}',
     25.00,
     10,
     0,
     'DRAFT',
     '{"game_id": 3, "round_duration": 20, "num_rounds": 3}',
     NOW()
   );
   -- ID retourné : 7

   -- Table: events_event_languages (relation ManyToMany)
   INSERT INTO events_event_languages (event_id, language_id)
   VALUES (7, 4), (7, 1);  -- de, fr

   -- Table: audit_auditlog
   INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
   VALUES (
     1,
     'CREATE',
     'Event',
     7,
     '{"status": "DRAFT", "title": "Atelier Allemand intensif"}',
     NOW()
   );
   ```

**Code Backend** : `backend/events/views.py`
```python
class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for Event CRUD operations."""

    def perform_create(self, serializer):
        """Create event with current user as organizer."""
        # Vérification : utilisateur doit être staff
        if not self.request.user.is_staff:
            raise PermissionDenied("Only staff members can create events")

        # Création via le service
        event_data = serializer.validated_data
        event = EventService.create_event(
            organizer=self.request.user,
            title=event_data['title'],
            description=event_data['description'],
            date=event_data['date'],
            location=event_data['location'],
            price=event_data['price'],
            max_participants=event_data['max_participants'],
            languages=event_data['languages'],
            game_config=event_data.get('game_config')
        )

        # Log d'audit
        AuditService.log_action(
            user=self.request.user,
            action='CREATE',
            model_name='Event',
            object_id=event.id,
            changes={'status': 'DRAFT', 'title': event.title}
        )

        return event
```

---

#### PUT `/api/v1/events/{id}/publish/` - Publication d'un événement

**Description** : Publier un événement en statut DRAFT pour le rendre visible aux membres.

**Démonstration avec Postman** :

1. **Configuration de la requête**
   ```
   Method: PUT
   URL: http://localhost:8000/api/v1/events/7/publish/
   Headers:
     Content-Type: application/json
     Authorization: Bearer <admin_token>
   ```

2. **Body** : Aucun body nécessaire

3. **Réponse attendue** (Status: 200 OK)
   ```json
   {
     "id": 7,
     "status": "PUBLISHED",
     "published_at": "2025-11-12T16:50:00Z",
     "message": "Event published successfully"
   }
   ```

4. **Réponse en cas d'erreur** (Status: 400 Bad Request)
   ```json
   {
     "detail": "Only draft events can be published"
   }
   ```
   OU
   ```json
   {
     "detail": "Cannot publish event with past date"
   }
   ```

5. **Base de données - Impact** :
   ```sql
   -- Avant publication :
   SELECT id, title, status, published_at
   FROM events_event
   WHERE id = 7;
   /*
   id | title                    | status | published_at
   7  | Atelier Allemand intensif| DRAFT  | NULL
   */

   -- Mise à jour
   UPDATE events_event
   SET status = 'PUBLISHED',
       published_at = NOW()
   WHERE id = 7;

   -- Après publication :
   SELECT id, title, status, published_at
   FROM events_event
   WHERE id = 7;
   /*
   id | title                    | status    | published_at
   7  | Atelier Allemand intensif| PUBLISHED | 2025-11-12 16:50:00
   */

   -- Log d'audit
   INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
   VALUES (
     1,
     'UPDATE',
     'Event',
     7,
     '{"status": {"old": "DRAFT", "new": "PUBLISHED"}}',
     NOW()
   );
   ```

**Code Backend** : `backend/events/views.py`
```python
@action(detail=True, methods=['put'])
def publish(self, request, pk=None):
    """Publish a draft event."""
    event = self.get_object()

    # Vérification : seul l'organisateur peut publier
    if event.organizer != request.user:
        raise PermissionDenied("Only the organizer can publish this event")

    try:
        event = EventService.publish_event(event)

        # Log d'audit
        AuditService.log_action(
            user=request.user,
            action='UPDATE',
            model_name='Event',
            object_id=event.id,
            changes={
                'status': {
                    'old': 'DRAFT',
                    'new': 'PUBLISHED'
                }
            }
        )

        return Response({
            'id': event.id,
            'status': event.status,
            'published_at': event.published_at,
            'message': 'Event published successfully'
        })

    except ValidationError as e:
        return Response(
            {'detail': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

---

#### DELETE `/api/v1/bookings/{id}/` - Annulation d'une réservation

**Description** : Annuler une réservation confirmée (avec remboursement automatique).

**Démonstration avec Postman** :

1. **Configuration de la requête**
   ```
   Method: DELETE
   URL: http://localhost:8000/api/v1/bookings/1/
   Headers:
     Content-Type: application/json
     Authorization: Bearer <user_token>
   ```

2. **Réponse attendue** (Status: 204 No Content)
   - Aucun contenu dans la réponse
   - La réservation est annulée et remboursée

3. **Réponse en cas d'erreur** (Status: 400 Bad Request)
   ```json
   {
     "detail": "Cannot cancel booking less than 24 hours before event"
   }
   ```
   OU
   ```json
   {
     "detail": "Only confirmed bookings can be cancelled"
   }
   ```

4. **Base de données - Impact** :
   ```sql
   -- Avant annulation :
   SELECT id, user_id, event_id, status, amount, payment_intent_id
   FROM bookings_booking
   WHERE id = 1;
   /*
   id | user_id | event_id | status    | amount | payment_intent_id
   1  | 2       | 1        | CONFIRMED | 15.00  | pi_1ABC123xyz
   */

   -- Mise à jour
   UPDATE bookings_booking
   SET status = 'CANCELLED',
       cancelled_at = NOW(),
       refund_id = 're_1XYZ789abc'
   WHERE id = 1;

   -- Libération de la place
   UPDATE events_event
   SET current_participants = current_participants - 1
   WHERE id = 1;

   -- Après annulation :
   SELECT id, user_id, event_id, status, amount, refund_id
   FROM bookings_booking
   WHERE id = 1;
   /*
   id | user_id | event_id | status    | amount | refund_id
   1  | 2       | 1        | CANCELLED | 15.00  | re_1XYZ789abc
   */

   -- Log d'audit
   INSERT INTO audit_auditlog (user_id, action, model_name, object_id, changes, timestamp)
   VALUES (
     2,
     'UPDATE',
     'Booking',
     1,
     '{"status": {"old": "CONFIRMED", "new": "CANCELLED"}}',
     NOW()
   );
   ```

**Code Backend** : `backend/bookings/views.py`
```python
class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for Booking operations."""

    def destroy(self, request, *args, **kwargs):
        """Cancel a booking (soft delete with refund)."""
        booking = self.get_object()

        # Vérification : seul le propriétaire peut annuler
        if booking.user != request.user:
            return Response(
                {'detail': 'You can only cancel your own bookings'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Annulation via le service (avec remboursement)
            BookingService.cancel_booking(booking)

            # Log d'audit
            AuditService.log_action(
                user=request.user,
                action='UPDATE',
                model_name='Booking',
                object_id=booking.id,
                changes={'status': {'old': 'CONFIRMED', 'new': 'CANCELLED'}}
            )

            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
```

---

## 5. Procédure de Désinscription

### 5.1 Contexte et Objectifs

**Objectif** : Permettre à un utilisateur de supprimer son compte tout en respectant :
- ✅ Les contraintes métier (réservations actives, événements organisés)
- ✅ Le RGPD (droit à l'oubli, anonymisation des données)
- ✅ L'intégrité des données (préservation des clés étrangères)

**Deux options disponibles** :

| Caractéristique | Désactivation | Suppression Permanente |
|-----------------|---------------|------------------------|
| **Réversibilité** | ✅ Réversible | ❌ Irréversible |
| **Données conservées** | ✅ Toutes | ❌ Anonymisées |
| **Email disponible** | ❌ Réservé | ✅ Libéré |
| **Réactivation** | ✅ À la connexion | ❌ Impossible |
| **Nouvelle inscription** | ❌ Bloquée | ✅ Autorisée |
| **Réservations historiques** | ✅ Conservées | ⚠️ Anonymisées |
| **Conformité RGPD** | ⚠️ Partielle | ✅ Complète |

---

### 5.2 Scénario : Utilisateur avec transactions actives

#### Profil de l'utilisateur de test

**Marie Dupont** :
```
ID : 2
Email : marie.dupont@example.com
Compte créé : 10 novembre 2025
Dernière connexion : 12 novembre 2025

Réservations :
  ✅ Réservation #1 - CONFIRMED
     Événement : "Échange linguistique Français-Anglais" (ID: 1)
     Date : 15 décembre 2025 à 19h00
     Montant payé : 15,00 EUR
     Payment Intent : pi_1ABC123xyz

  ❌ Réservation #2 - CANCELLED
     Événement : "Conversation Espagnol débutants" (ID: 3)
     Date : 20 novembre 2025 à 18h30
     Montant remboursé : 12,00 EUR

Historique :
  - 2 réservations créées
  - 1 paiement confirmé
  - 1 annulation effectuée
  - 15 connexions au total
```

---

### 5.3 Tentative de suppression avec réservations actives

**Démonstration** :

1. **Accès à la page profil**
   - Connexion en tant que Marie
   - URL : `http://localhost:4200/fr/profile`
   - Sections visibles :
     ```
     📋 Informations du compte
     - Email : marie.dupont@example.com
     - Nom complet : Marie Dupont
     - Âge : 25 ans
     - Membre depuis : 10 novembre 2025

     ⚠️ Zone dangereuse
     [Désactiver mon compte]
     [Supprimer définitivement mon compte]
     ```

2. **Tentative de suppression permanente**
   - Cliquer sur "Supprimer définitivement mon compte"
   - Modal d'avertissement :
     ```
     ⚠️ ATTENTION : Cette action est IRRÉVERSIBLE !

     Conséquences :
     - Toutes vos données personnelles seront anonymisées
     - Votre email sera remplacé par deleted_user_2@deleted.local
     - Vous ne pourrez JAMAIS réactiver ce compte
     - Cette action est IRRÉVERSIBLE

     Mot de passe :
     [__________________]

     [Annuler] [Confirmer la suppression]
     ```

3. **Saisie du mot de passe et confirmation**
   - Mot de passe : `MotDePasse123!`
   - Cliquer sur "Confirmer la suppression"

4. **Réponse attendue : Erreur**
   ```
   ❌ Impossible de supprimer le compte

   Vous avez des réservations confirmées à venir.
   Veuillez les annuler d'abord.

   Réservations concernées :
   - Échange linguistique Français-Anglais (15/12/2025)

   [Voir mes réservations] [Fermer]
   ```

**Code Backend - Vérification** : `backend/users/services/auth_service.py:161-190`
```python
@staticmethod
@transaction.atomic
def permanently_delete_account(user):
    """Permanently delete user account (anonymize all personal data)."""
    from django.utils import timezone
    from bookings.models import Booking, BookingStatus
    from events.models import Event

    now = timezone.now()

    # Check for upcoming confirmed bookings
    upcoming_bookings = Booking.objects.filter(
        user=user,
        status=BookingStatus.CONFIRMED,
        event__date__gte=now
    ).exists()

    if upcoming_bookings:
        return False, "Cannot delete account: you have upcoming confirmed bookings. Please cancel them first."

    # Check for upcoming published events as organizer
    upcoming_events = Event.objects.filter(
        organizer=user,
        status=Event.Status.PUBLISHED,
        date__gte=now
    ).exists()

    if upcoming_events:
        return False, "Cannot delete account: you are organizing upcoming published events. Please cancel them first."

    # Proceed with permanent deletion...
```

---

### 5.4 Annulation des réservations actives

**Démonstration** :

1. **Navigation vers "Mes Réservations"**
   - Cliquer sur "Voir mes réservations" dans le message d'erreur
   - URL : `http://localhost:4200/fr/bookings`
   - Affichage de toutes les réservations

2. **Identification de la réservation active**
   ```
   🎫 Réservation #1 - ✅ CONFIRMÉE

   Événement : Échange linguistique Français-Anglais
   📅 Date : Vendredi 15 décembre 2025 à 19h00
   📍 Lieu : 123 Rue de la Paix, 75002 Paris
   💰 Montant payé : 15,00 EUR

   [Voir l'événement] [Annuler ma réservation]
   ```

3. **Annulation de la réservation**
   - Cliquer sur "Annuler ma réservation"
   - Confirmation :
     ```
     ⚠️ Annuler votre réservation ?

     Vous êtes sur le point d'annuler votre réservation pour :
     "Échange linguistique Français-Anglais"

     - Un remboursement complet sera effectué (15,00 EUR)
     - Vous recevrez un email de confirmation
     - Cette action ne peut pas être annulée

     [Retour] [Confirmer l'annulation]
     ```

4. **Confirmation de l'annulation**
   - Cliquer sur "Confirmer l'annulation"
   - ✅ Remboursement automatique via Stripe
   - ✅ Statut : CONFIRMED → CANCELLED
   - ✅ Place libérée dans l'événement (8 → 9 places disponibles)
   - ✅ Message : "Votre réservation a été annulée avec succès. Vous serez remboursé sous 5-10 jours ouvrés."

5. **Vérification de la base de données**
   ```sql
   -- Avant annulation :
   SELECT id, user_id, event_id, status, payment_intent_id, refund_id
   FROM bookings_booking
   WHERE id = 1;
   /*
   id | user_id | event_id | status    | payment_intent_id | refund_id
   1  | 2       | 1        | CONFIRMED | pi_1ABC123xyz     | NULL
   */

   -- Après annulation :
   SELECT id, user_id, event_id, status, payment_intent_id, refund_id, cancelled_at
   FROM bookings_booking
   WHERE id = 1;
   /*
   id | user_id | event_id | status    | payment_intent_id | refund_id        | cancelled_at
   1  | 2       | 1        | CANCELLED | pi_1ABC123xyz     | re_1XYZ789abc    | 2025-11-12 17:00:00
   */

   -- Vérification de la place libérée :
   SELECT id, title, current_participants, max_participants
   FROM events_event
   WHERE id = 1;
   /*
   id | title                              | current_participants | max_participants
   1  | Échange linguistique Français-Anglais | 7                  | 20
   */
   ```

---

### 5.5 Suppression permanente réussie

**Démonstration** :

1. **Retour à la page profil**
   - URL : `http://localhost:4200/fr/profile`
   - Toutes les réservations sont maintenant annulées ou passées

2. **Nouvelle tentative de suppression permanente**
   - Cliquer sur "Supprimer définitivement mon compte"
   - Modal d'avertissement (identique)
   - Saisir le mot de passe : `MotDePasse123!`
   - Cliquer sur "Confirmer la suppression"

3. **Processus de suppression**
   - ✅ Vérification réussie (aucune réservation active)
   - ✅ Anonymisation de toutes les données personnelles
   - ✅ Email changé : `deleted_user_2@deleted.local`
   - ✅ Mot de passe rendu inutilisable
   - ✅ Langues effacées
   - ✅ Déconnexion automatique
   - ✅ Redirection vers la page de connexion
   - ✅ Message : "Votre compte a été supprimé définitivement."

4. **État de la base de données**

**Avant suppression** :
```sql
SELECT id, email, first_name, last_name, age, bio, is_active,
       latitude, longitude, address, city, country
FROM users_user
WHERE id = 2;
```

| id | email | first_name | last_name | age | bio | is_active | latitude | longitude | address | city | country |
|----|-------|------------|-----------|-----|-----|-----------|----------|-----------|---------|------|---------|
| 2 | marie.dupont@example.com | Marie | Dupont | 25 | "Passionnée de langues..." | true | 48.8566 | 2.3522 | "10 Rue..." | "Paris" | "France" |

**Après suppression permanente** :
```sql
SELECT id, email, first_name, last_name, age, bio, is_active,
       latitude, longitude, address, city, country
FROM users_user
WHERE id = 2;
```

| id | email | first_name | last_name | age | bio | is_active | latitude | longitude | address | city | country |
|----|-------|------------|-----------|-----|-----|-----------|----------|-----------|---------|------|---------|
| 2 | deleted_user_2@deleted.local | Deleted | User | NULL | "" | false | NULL | NULL | "" | "" | "" |

**Langues (relation ManyToMany)** :
```sql
-- Avant :
SELECT user_id, language_id
FROM users_user_native_langs
WHERE user_id = 2;
/*
user_id | language_id
2       | 1  (fr - Français)
*/

SELECT user_id, language_id
FROM users_user_target_langs
WHERE user_id = 2;
/*
user_id | language_id
2       | 2  (en - English)
*/

-- Après : tables vidées
SELECT COUNT(*) FROM users_user_native_langs WHERE user_id = 2;
/* 0 */

SELECT COUNT(*) FROM users_user_target_langs WHERE user_id = 2;
/* 0 */
```

**Réservations (clés étrangères préservées)** :
```sql
-- Les réservations existent toujours (intégrité des données)
SELECT b.id, b.user_id, b.event_id, b.status, b.amount,
       u.email, u.first_name, u.last_name
FROM bookings_booking b
JOIN users_user u ON b.user_id = u.id
WHERE b.user_id = 2;
```

| id | user_id | event_id | status | amount | email | first_name | last_name |
|----|---------|----------|--------|--------|-------|------------|-----------|
| 1 | 2 | 1 | CANCELLED | 15.00 | deleted_user_2@deleted.local | Deleted | User |
| 2 | 2 | 3 | CANCELLED | 12.00 | deleted_user_2@deleted.local | Deleted | User |

✅ **Toutes les réservations sont anonymisées mais conservées pour l'intégrité des données.**

**Code Backend - Anonymisation** : `backend/users/services/auth_service.py:161-213`
```python
@staticmethod
@transaction.atomic
def permanently_delete_account(user):
    """Permanently delete user account (anonymize all personal data)."""
    # ... vérifications des réservations actives ...

    # Anonymize all personal data (GDPR compliant)
    user_id = user.id
    user.email = f"deleted_user_{user_id}@deleted.local"
    user.first_name = "Deleted"
    user.last_name = "User"
    user.bio = ""
    user.avatar = ""
    user.address = ""
    user.city = ""
    user.country = ""
    user.latitude = None
    user.longitude = None
    user.age = None
    user.is_active = False
    user.consent_given = False
    user.consent_given_at = None

    # Clear password (set unusable)
    user.set_unusable_password()

    # Clear language preferences
    user.native_langs.clear()
    user.target_langs.clear()

    user.save()

    # Log d'audit
    AuditService.log_action(
        user=user,
        action='DELETE',
        model_name='User',
        object_id=user.id,
        changes={
            'anonymized': True,
            'email': f'deleted_user_{user_id}@deleted.local'
        }
    )

    return True, None
```

---

### 5.6 Impact sur les logs d'audit

**Vérification des logs** :
```sql
SELECT id, user_id, action, model_name, object_id,
       changes, timestamp
FROM audit_auditlog
WHERE user_id = 2
ORDER BY timestamp DESC
LIMIT 10;
```

**Résultat** :
```
id  | user_id | action | model_name | object_id | changes | timestamp
----|---------|--------|------------|-----------|---------|--------------------
155 | 2       | DELETE | User       | 2         | {"anonymized": true, "email": "deleted_user_2@deleted.local"} | 2025-11-12 17:05:00
154 | 2       | UPDATE | Booking    | 1         | {"status": {"old": "CONFIRMED", "new": "CANCELLED"}} | 2025-11-12 17:00:00
153 | 2       | UPDATE | Booking    | 1         | {"status": {"old": "PENDING", "new": "CONFIRMED"}} | 2025-11-10 14:31:00
152 | 2       | CREATE | Booking    | 1         | {"event_id": 1, "amount": "15.00", "status": "PENDING"} | 2025-11-10 14:30:00
151 | 2       | UPDATE | Booking    | 2         | {"status": {"old": "CONFIRMED", "new": "CANCELLED"}} | 2025-11-08 16:20:00
150 | 2       | UPDATE | Booking    | 2         | {"status": {"old": "PENDING", "new": "CONFIRMED"}} | 2025-11-05 10:05:00
149 | 2       | CREATE | Booking    | 2         | {"event_id": 3, "amount": "12.00", "status": "PENDING"} | 2025-11-05 10:00:00
```

✅ **Tous les logs d'audit sont préservés** pour la conformité RGPD et la traçabilité légale.

---

### 5.7 Tentative de réinscription

**Démonstration** :

1. **Tentative d'inscription avec l'ancien email**
   - URL : `http://localhost:4200/fr/auth/register`
   - Email : `marie.dupont@example.com`
   - Prénom : Marie
   - Nom : Dupont
   - ✅ **Inscription autorisée** (l'email est maintenant disponible)
   - ✅ **Nouveau compte créé** (ID différent : 10, données vierges)
   - ✅ Message : "Compte créé avec succès !"

2. **Tentative de connexion avec l'ancien mot de passe**
   - URL : `http://localhost:4200/fr/auth/login`
   - Email : `marie.dupont@example.com`
   - Mot de passe : `MotDePasse123!` (ancien mot de passe)
   - ❌ **Erreur : "Identifiants invalides"**
   - Raison : C'est un nouveau compte avec un nouveau mot de passe

**Comparaison base de données** :
```sql
-- Ancien compte (anonymisé, ID: 2)
SELECT id, email, first_name, last_name, is_active, date_joined
FROM users_user
WHERE id = 2;
/*
id | email                        | first_name | last_name | is_active | date_joined
2  | deleted_user_2@deleted.local | Deleted    | User      | false     | 2025-11-10 14:30:00
*/

-- Nouveau compte (nouvelles données, ID: 10)
SELECT id, email, first_name, last_name, is_active, date_joined
FROM users_user
WHERE email = 'marie.dupont@example.com';
/*
id | email                    | first_name | last_name | is_active | date_joined
10 | marie.dupont@example.com | Marie      | Dupont    | true      | 2025-11-12 17:10:00
*/

-- Vérification : ce sont bien 2 comptes différents
SELECT COUNT(*) as total_users, COUNT(DISTINCT id) as distinct_ids
FROM users_user
WHERE email IN ('marie.dupont@example.com', 'deleted_user_2@deleted.local');
/*
total_users | distinct_ids
2           | 2
*/
```

✅ **L'utilisateur peut créer un nouveau compte avec le même email, mais c'est un compte complètement différent sans aucun lien avec l'ancien.**

---

### 5.8 Alternative : Désactivation (réversible)

**Démonstration de la désactivation** :

1. **Utilisateur : Jean Martin**
   ```
   Email : jean.martin@example.com
   ID : 3
   Réservations : Aucune réservation active
   ```

2. **Désactivation du compte**
   - URL : `http://localhost:4200/fr/profile`
   - Cliquer sur "Désactiver mon compte" (première option)
   - Modal :
     ```
     ⚠️ Désactiver votre compte ?

     Votre compte sera temporairement désactivé.
     Vous pourrez le réactiver en vous reconnectant.

     Conséquences :
     - Vous ne pourrez plus vous connecter
     - Vos données seront conservées
     - Vous pouvez réactiver votre compte à tout moment

     Mot de passe :
     [__________________]

     [Annuler] [Confirmer]
     ```
   - Saisir le mot de passe
   - ✅ Compte désactivé (`is_active=False`)
   - ✅ **Toutes les données sont conservées**

3. **Vérification base de données**
   ```sql
   -- Après désactivation :
   SELECT id, email, first_name, last_name, is_active, age, bio
   FROM users_user
   WHERE email = 'jean.martin@example.com';
   /*
   id | email                   | first_name | last_name | is_active | age | bio
   3  | jean.martin@example.com | Jean       | Martin    | false     | 30  | "Voyageur passionné..."
   */
   ```

4. **Tentative d'inscription**
   - URL : `http://localhost:4200/fr/auth/register`
   - Email : `jean.martin@example.com`
   - ❌ **Erreur : "Cet email est déjà utilisé"**

5. **Réactivation par connexion**
   - URL : `http://localhost:4200/fr/auth/login`
   - Email : `jean.martin@example.com`
   - Mot de passe : (ancien mot de passe)
   - ✅ **Connexion réussie**
   - ✅ **Compte réactivé automatiquement** (`is_active=True`)
   - ✅ Message : "Bon retour ! Votre compte a été réactivé avec succès."
   - ✅ **Toutes les données restaurées** (réservations, préférences, etc.)

**Vérification base de données après réactivation** :
```sql
SELECT id, email, first_name, last_name, is_active, age, bio
FROM users_user
WHERE email = 'jean.martin@example.com';
/*
id | email                   | first_name | last_name | is_active | age | bio
3  | jean.martin@example.com | Jean       | Martin    | true      | 30  | "Voyageur passionné..."
*/
```

✅ **Toutes les données sont intactes après la réactivation.**

---

### 5.9 Code complet de la suppression

**Frontend - Composant** : `frontend/src/app/features/profile/profile.component.ts:88-128`
```typescript
confirmDeleteAccount() {
  const password = this.deletePassword();

  if (!password) {
    this.deleteError.set('PASSWORD_REQUIRED');
    return;
  }

  this.deleteLoading.set(true);
  this.deleteError.set(null);

  // Choix de la méthode selon le type de suppression
  const deleteMethod = this.deletionType() === 'deactivate'
    ? this.authApi.deactivateAccount(password)
    : this.authApi.permanentlyDeleteAccount(password);

  deleteMethod.subscribe({
    next: () => {
      this.deleteLoading.set(false);
      // Déconnexion et redirection
      this.tokens.clear();
      this.router.navigate(['/', this.lang, 'auth', 'login']);
    },
    error: (err) => {
      console.error('Delete account error:', err);
      this.deleteLoading.set(false);

      const errorDetail = err?.error?.detail || '';
      let errorKey = 'PROFILE.DELETE_ACCOUNT_ERROR';

      // Mapping des erreurs
      if (errorDetail.includes('upcoming confirmed bookings')) {
        errorKey = 'PROFILE.CANNOT_DELETE_WITH_BOOKINGS';
      } else if (errorDetail.includes('organizing upcoming published events')) {
        errorKey = 'PROFILE.CANNOT_DELETE_WITH_EVENTS';
      } else if (errorDetail.includes('Invalid password')) {
        errorKey = 'auth.errors.bad_credentials';
      }

      this.deleteError.set(errorKey);
    }
  });
}
```

**Frontend - Service API** : `frontend/src/app/core/http/services/auth-api.service.ts`
```typescript
deactivateAccount(password: string) {
  return this.http.request('delete', `${this.base}/auth/deactivate-account/`, {
    body: { password }
  });
}

permanentlyDeleteAccount(password: string) {
  return this.http.request('delete', `${this.base}/auth/permanently-delete-account/`, {
    body: { password }
  });
}
```

---

## Conclusion

Cette documentation démontre le bon fonctionnement complet de l'application Conversa, incluant :

✅ **Fonctionnalités business principales**
- Réservation et paiement d'événements linguistiques
- Création et publication d'événements (administrateur)
- Gestion des participants et annulations
- Système de paiement Stripe complet avec webhooks

✅ **Fonctionnalités pertinentes**
- Intégration Stripe (Payment Intent, remboursements, webhooks)
- Système de réservations avec 4 statuts (PENDING, CONFIRMED, CANCELLED, REFUNDED)
- Logs d'audit complets pour traçabilité et conformité

✅ **Multilinguisme**
- Support FR/EN/NL complet (2500+ clés de traduction)
- Changement de langue dynamique
- Traductions frontend et backend (emails)

✅ **API REST**
- Endpoints GET (liste événements, mes réservations)
- Endpoints POST (création événement, réservation)
- Endpoints PUT (publication événement)
- Endpoints DELETE (annulation réservation)

✅ **Gestion de la désinscription**
- Deux options (désactivation réversible / suppression permanente irréversible)
- Vérification des contraintes métier (réservations actives)
- Conformité RGPD (anonymisation complète)
- Impact détaillé sur la base de données
- Préservation de l'intégrité des données
- Logs d'audit conservés

Tous les codes sources, commandes SQL, captures d'écran et exemples Postman ont été fournis pour faciliter la démonstration complète de l'application.
