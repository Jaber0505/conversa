"""
Script to generate comprehensive fixtures for Conversa.

Generates:
- 100 users (30 organizers, 70 participants)
- Events distributed from yesterday to +7 days (exactly 100 events over 8 days)
- Bookings capped at 6 reservations per event (organizer included)

Usage:
    python generate_fixtures.py --start-date 2025-12-01
    (Events will be generated from 2025-11-30 to 2025-12-08)
"""

import json
import random
import secrets
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
START_USER_ID = 11  # After existing users
NUM_USERS = 100
NUM_ORGANIZERS = 30
NUM_PARTICIPANTS = NUM_USERS - NUM_ORGANIZERS
TARGET_NUM_EVENTS = 100

# Languages that currently have game content (matching fixtures/games/*_<code>.json)
# IDs correspond to backend/fixtures/01_languages.json
SUPPORTED_LANGUAGE_IDS = [1, 2, 4]  # fr, en, nl
SUPPORTED_LANGUAGE_CODES = {"fr", "en", "nl"}

# Password hash for "password123" (same as existing fixtures)
PASSWORD_HASH = "pbkdf2_sha256$600000$fixturesalt$3co5kYNgw2jX+vtNl2uThvUopcuX/aIYa24sBV7KXPU="

# Belgian cities with real addresses
CITIES = [
    "Bruxelles", "Anvers", "Gand", "Charleroi", "Liège",
    "Bruges", "Namur", "Louvain", "Mons", "Malines"
]

# Real Belgian partner venues (bars, cafés, restaurants)
PARTNER_NAMES = [
    "Le Café Central", "Brasserie de la Gare", "L'Atelier du Coin",
    "Chez Marie", "Le Comptoir", "La Terrasse", "Le Zinc",
    "Café des Arts", "Le Relais", "La Brasserie Royale",
    "Le Bistrot", "Café de la Place", "Le Petit Bruxelles",
    "L'Auberge Flamande", "Le Grand Café", "La Taverne",
    "Le Pub Irlandais", "Café du Marché", "Le Bar à Vins",
    "La Brasserie Belge", "Le Coin Convivial", "Café des Amis",
    "Le Troquet", "La Guinguette", "Le Bar Central",
    "Café de la Paix", "Le Refuge", "La Maison du Peuple",
    "Le Café Liégeois", "Brasserie du Parc", "Le Petit Zinc",
    "Café de l'Avenue", "Le Bar des Sportifs", "La Choperie",
    "Le Café du Théâtre", "Brasserie de l'Europe", "Le Drinking",
    "Café Bruxellois", "Le Bar Flamand", "La Taverne Anversoise",
    "Le Coin des Artistes", "Café de la Montagne", "Le Grand Zinc",
    "Brasserie du Centre", "Le Petit Café", "La Maison Bleue",
    "Café des Sports", "Le Bar du Coin", "La Brasserie du Nord",
    "Le Café Wallon", "Pub Saint-Michel", "Le Zinc Doré"
]

# Real Belgian streets
STREET_NAMES = [
    "Rue Neuve", "Boulevard Anspach", "Rue Antoine Dansaert", "Chaussée d'Ixelles",
    "Avenue Louise", "Rue de la Loi", "Boulevard du Midi", "Rue Royale",
    "Place de Brouckère", "Rue du Marché aux Herbes", "Chaussée de Waterloo",
    "Boulevard de Waterloo", "Rue des Bouchers", "Place Saint-Géry",
    "Rue de Flandre", "Avenue de la Toison d'Or", "Chaussée de Charleroi",
    "Rue du Bailli", "Avenue des Arts", "Boulevard du Régent",
    "Rue Haute", "Rue Blaes", "Place du Jeu de Balle", "Chaussée de Wavre",
    "Rue de Namur", "Boulevard de l'Empereur", "Rue du Midi",
    "Place de la Monnaie", "Rue des Pierres", "Rue de la Montagne",
    "Boulevard du Jardin Botanique", "Chaussée de Louvain", "Avenue de Tervueren",
    "Rue Archimède", "Rue de Trèves", "Boulevard Charlemagne",
    "Place Flagey", "Chaussée de Boondael", "Avenue Général de Gaulle",
    "Boulevard du Triomphe", "Avenue Franklin Roosevelt", "Place Poelaert",
    "Rue de la Régence", "Place Royale", "Rue du Grand Sablon",
    "Rue des Sablons", "Chaussée de Forest", "Avenue Brugmann",
    "Rue Vanderkindere", "Boulevard de la Cambre", "Avenue Molière"
]

# Brussels communes and neighborhoods
BRUSSELS_AREAS = [
    "Bruxelles Centre", "Ixelles", "Etterbeek", "Schaerbeek",
    "Saint-Gilles", "Forest", "Uccle", "Woluwe-Saint-Pierre",
    "Woluwe-Saint-Lambert", "Auderghem", "Watermael-Boitsfort",
    "Anderlecht", "Molenbeek", "Koekelberg", "Jette",
    "Ganshoren", "Berchem-Sainte-Agathe", "Evere", "Saint-Josse"
]

# First names pool
FIRST_NAMES = [
    "Alice", "Bob", "Carla", "Diego", "Emma", "Farid", "Giulia", "Hugo",
    "Inès", "Jacques", "Karim", "Laura", "Marc", "Nina", "Oscar", "Paula",
    "Quentin", "Rosa", "Simon", "Tina", "Ugo", "Vera", "William", "Xenia",
    "Yves", "Zoé", "Adrien", "Beatrice", "Cédric", "Diane", "Emile", "Fanny",
    "Gabriel", "Hélène", "Ivan", "Julie", "Kevin", "Louise", "Mathieu", "Nora",
    "Olivier", "Patricia", "Raphaël", "Sophie", "Thomas", "Ursula", "Vincent",
    "Wendy", "Xavier", "Yasmine", "Zachary", "Amélie", "Bruno", "Céline",
    "Damien", "Elise", "François", "Gisèle", "Henri", "Isabelle", "Jean",
    "Karine", "Luc", "Marie", "Nicolas", "Odile", "Pierre", "Rachel", "Serge",
    "Thérèse", "Urbain", "Valérie", "Yannick", "Zoé", "Antoine", "Brigitte",
    "Claude", "Denise", "Eric", "Florence", "Georges", "Hélène", "Igor",
    "Jeanne", "Karl", "Laure", "Michel", "Nadine", "Olivier", "Pauline",
    "René", "Sylvie", "Thierry", "Valérie", "Willy", "Yvette", "Alain",
    "Bernadette", "Christian", "Dominique", "Etienne", "Françoise"
]

# Last names pool
LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
    "Girard", "André", "Mercier", "Dupont", "Lambert", "Bonnet", "François",
    "Martinez", "Legrand", "Garnier", "Faure", "Rousseau", "Blanc", "Guerin",
    "Muller", "Henry", "Roussel", "Nicolas", "Perrin", "Morin", "Mathieu",
    "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin",
    "Masson", "Sanchez", "Gerard", "Nguyen", "Boyer", "Denis", "Lemaire",
    "Duval", "Joly", "Gautier", "Roger", "Roy", "Noel", "Meyer", "Lucas",
    "Meunier", "Jean", "Perez", "Marchand", "Dufour", "Blanchard", "Marie",
    "Barbier", "Brun", "Dumas", "Brunet", "Schmitt", "Leroux", "Colin",
    "Fernandez", "Renard", "Arnaud", "Rolland", "Caron", "Aubert", "Giraud",
    "Leclerc", "Vidal", "Bourgeois", "Renaud", "Lemoine", "Picard", "Gaillard",
    "Philippe", "Leclercq", "Lacroix", "Fabre", "Dupuis", "Olivier", "Rodriguez"
]

# Event themes
EVENT_THEMES = [
    "Afterwork – brise-glace",
    "Coffee chat – small talk",
    "Apéro vocab – voyages",
    "Jeux de rôle – restaurant",
    "Speed chat – présentations",
    "Debate night – tech & IA",
    "Jeux – Taboo & Guess Who",
    "Conversa Quiz – culture",
    "Business English – pitch",
    "Conversation libre – actu",
    "Atelier grammaire",
    "Soirée ciné-débat",
    "Brunch linguistique",
    "Karaoke multilingue",
    "Jeux de société",
    "Apéro networking",
    "Workshop prononciation",
    "Table ronde – politique",
    "Atelier cuisine & langue",
    "Speed dating linguistique"
]


def generate_partners():
    """Generate 100 partner fixtures with real Belgian addresses."""
    partners = []
    used_names = set()

    for i in range(100):
        partner_id = i + 1

        # Get unique partner name
        while True:
            name = random.choice(PARTNER_NAMES)
            if name not in used_names:
                used_names.add(name)
                break
            # If all names used, add suffix
            if len(used_names) >= len(PARTNER_NAMES):
                name = f"{random.choice(PARTNER_NAMES)} {random.choice(['Centre', 'Nord', 'Sud', 'Est', 'Ouest'])}"
                break

        # Generate realistic Brussels address
        street_number = random.randint(1, 300)
        street_name = random.choice(STREET_NAMES)
        # Brussels postal codes only
        postal_code = random.choice([1000, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090,
                                     1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210])
        city_area = random.choice(BRUSSELS_AREAS)
        address = f"{street_name} {street_number}, {postal_code} {city_area}, Belgique"

        # Random reputation (3.0 to 5.0)
        reputation = round(random.uniform(3.0, 5.0), 1)

        # Random capacity (10 to 40)
        capacity = random.randint(10, 40)

        # 95% active, 5% inactive
        is_active = random.random() < 0.95

        # Creation date (spread over last 2 years)
        days_ago = random.randint(1, 730)
        created_at = (datetime.now() - timedelta(days=days_ago)).isoformat() + "Z"

        partner = {
            "model": "partners.partner",
            "pk": partner_id,
            "fields": {
                "name": name,
                "address": address,
                "city": city_area,
                "reputation": reputation,
                "capacity": capacity,
                "is_active": is_active,
                "api_key": secrets.token_hex(32),
                "created_at": created_at,
                "updated_at": created_at
            }
        }
        partners.append(partner)

    return partners


def generate_users():
    """Generate 100 user fixtures (30 organizers, 70 participants)."""
    users = []
    target_langs_data = []
    target_lang_pk = 11  # Start after existing target languages

    for i in range(NUM_USERS):
        user_id = START_USER_ID + i
        is_organizer = i < NUM_ORGANIZERS

        # Generate unique email
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{user_id}@example.com"

        # Random age between 18 and 65
        age = random.randint(18, 65)

        # Random city
        city = random.choice(CITIES)

        # Random native language (1-4: FR, EN, NL, ES)
        native_lang = random.randint(1, 4)

        # Date joined (spread over last year)
        days_ago = random.randint(1, 365)
        date_joined = (datetime.now() - timedelta(days=days_ago)).isoformat() + "Z"

        user = {
            "model": "users.user",
            "pk": user_id,
            "fields": {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "bio": "",
                "avatar": "",
                "address": "",
                "city": city,
                "country": "BE",
                "latitude": None,
                "longitude": None,
                "consent_given": True,
                "consent_given_at": date_joined,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "date_joined": date_joined,
                "password": PASSWORD_HASH,
                "native_langs": [native_lang]
            }
        }
        users.append(user)

        # Add target language (different from native)
        target_lang = random.choice([l for l in [1, 2, 3, 4] if l != native_lang])
        target_langs_data.append({
            "model": "users.usertargetlanguage",
            "pk": target_lang_pk,
            "fields": {
                "user": user_id,
                "language": target_lang
            }
        })
        target_lang_pk += 1

    return users + target_langs_data


def generate_events(
    start_date_str,
    num_organizers=NUM_ORGANIZERS,
    target_events=TARGET_NUM_EVENTS,
):
    """
    Generate exactly target_events within an 8-day window from yesterday to +7 days.

    Events are distributed from yesterday (start_date - 1 day) to start_date + 7 days
    (inclusive), with start times between 12:00 and 21:00 inclusive.
    """
    events = []
    start_date = datetime.fromisoformat(start_date_str.replace("Z", ""))

    organizer_ids = list(range(START_USER_ID, START_USER_ID + num_organizers))
    if not organizer_ids:
        return events

    event_id = 11  # Start after existing events
    day_offsets = list(range(-1, 8))  # Ensure coverage from day -1 (yesterday) to day +7
    event_counter = 0

    while len(events) < target_events:
        for org_id in organizer_ids:
            if len(events) >= target_events:
                break

            # Each organizer creates 2-4 events per pass, limited by remaining target
            remaining = target_events - len(events)
            num_events = min(random.randint(2, 4), remaining)

            for _ in range(num_events):
                # Keep events within an 8-day window (yesterday to +7 days from start date)
                days_offset = day_offsets[event_counter % len(day_offsets)]
                event_date = start_date + timedelta(days=days_offset)

                # Random time between 12:00 and 21:00
                hour = random.randint(12, 21)
                minute = random.choice([0, 15, 30, 45])
                event_datetime = event_date.replace(hour=hour, minute=minute)

                # Random language (limited to those having game content), difficulty, theme
                language = random.choice(SUPPORTED_LANGUAGE_IDS)
                difficulty = random.choice(["easy", "medium", "hard"])
                theme = random.choice(EVENT_THEMES)

                # Random partner (1-100)
                partner = random.randint(1, 100)

                # Creation timestamp
                created_at = (
                    event_datetime - timedelta(days=random.randint(7, 30))
                ).isoformat() + "Z"

                # Determine status: FINISHED if event time has passed, PUBLISHED otherwise
                now = datetime.now()
                status = "FINISHED" if event_datetime < now else "PUBLISHED"

                event = {
                    "model": "events.event",
                    "pk": event_id,
                    "fields": {
                        "organizer": org_id,
                        "partner": partner,
                        "language": language,
                        "theme": theme,
                        "difficulty": difficulty,
                        "datetime_start": event_datetime.isoformat() + "Z",
                        "photo": None,
                        "title": f"Event {event_id}",
                        "address": "Rue Example, 1000, Bruxelles, BE",
                        "status": status,
                        "created_at": created_at,
                        "updated_at": created_at,
                        "price_cents": 700,
                        "min_participants": 3,
                        "max_participants": 6,
                        "is_draft_visible": True,
                        "organizer_paid_at": created_at,
                        "game_type": random.choice(
                            ["picture_description", "word_association"]
                        ),
                        "game_started": False,
                    },
                }
                events.append(event)
                event_id += 1
                event_counter += 1

    # Keep fixture order chronological within the 8-day window (yesterday to +7 days)
    events.sort(key=lambda e: e["fields"]["datetime_start"])

    return events


def generate_bookings(events):
    """Generate bookings capped by each event's max participants."""
    bookings = []
    booking_id = 1

    # All non-organizer users who can participate
    participant_ids = list(range(START_USER_ID + NUM_ORGANIZERS, START_USER_ID + NUM_USERS))

    for event in events:
        event_id = event["pk"]
        organizer_id = event["fields"]["organizer"]
        event_datetime = event["fields"]["datetime_start"]

        # Organizer's booking (is_organizer_booking=True)
        organizer_booking = {
            "model": "bookings.booking",
            "pk": booking_id,
            "fields": {
                "user": organizer_id,
                "event": event_id,
                "status": "CONFIRMED",
                "amount_cents": 700,
                "currency": "EUR",
                "is_organizer_booking": True,
                "expires_at": event_datetime,
                "payment_intent_id": f"pi_organizer_{booking_id}",
                "confirmed_at": event["fields"]["created_at"],
                "cancelled_at": None,
                "created_at": event["fields"]["created_at"],
                "updated_at": event["fields"]["created_at"]
            }
        }
        bookings.append(organizer_booking)
        booking_id += 1

        # Random participants while respecting max_participants cap (organizer already booked)
        max_slots = max(event["fields"]["max_participants"] - 1, 0)
        if max_slots == 0:
            continue

        min_required = min(event["fields"]["min_participants"], max_slots)
        min_required = max(1, min_required)
        num_participants = random.randint(min_required, max_slots)
        event_participants = random.sample(
            participant_ids, min(num_participants, len(participant_ids))
        )

        for participant_id in event_participants:
            # Random confirmation time (between creation and event start)
            confirmed_at = event["fields"]["created_at"]

            participant_booking = {
                "model": "bookings.booking",
                "pk": booking_id,
                "fields": {
                    "user": participant_id,
                    "event": event_id,
                    "status": "CONFIRMED",
                    "amount_cents": 700,
                    "currency": "EUR",
                    "is_organizer_booking": False,
                    "expires_at": event_datetime,
                    "payment_intent_id": f"pi_{booking_id}",
                    "confirmed_at": confirmed_at,
                    "cancelled_at": None,
                    "created_at": confirmed_at,
                    "updated_at": confirmed_at
                }
            }
            bookings.append(participant_booking)
            booking_id += 1

    return bookings


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Conversa fixtures")
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date for events (YYYY-MM-DD) - REQUIRED"
    )
    args = parser.parse_args()

    fixtures_dir = Path(__file__).parent

    print(f"[fixtures] Generating fixtures with start date: {args.start_date}")

    # Generate partners (overwrites 02_partners.json)
    print(" - Generating 100 partners...")
    partners_data = generate_partners()
    with open(fixtures_dir / "02_partners.json", "w", encoding="utf-8") as f:
        json.dump(partners_data, f, indent=2, ensure_ascii=False)
    print("   ✓ 100 partners generated with real Belgian addresses")

    # Generate users (overwrites 03_users.json)
    print(" - Generating 100 users...")
    users_data = generate_users()
    with open(fixtures_dir / "03_users.json", "w", encoding="utf-8") as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Generated {NUM_USERS} users ({NUM_ORGANIZERS} organizers, {NUM_PARTICIPANTS} participants)")

    # Generate events (overwrites 04_events.json)
    print(" - Generating events...")
    events_data = generate_events(args.start_date)
    with open(fixtures_dir / "04_events.json", "w", encoding="utf-8") as f:
        json.dump(events_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Generated {len(events_data)} events")

    # Generate bookings (creates 05_bookings.json)
    print(" - Generating bookings...")
    bookings_data = generate_bookings(events_data)
    with open(fixtures_dir / "05_bookings.json", "w", encoding="utf-8") as f:
        json.dump(bookings_data, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Generated {len(bookings_data)} bookings")

    print("\nFixtures generated successfully!")
    print("\nSummary:")
    print("   - Partners: 100 (with real Belgian addresses)")
    print(f"   - Users: {NUM_USERS} (30 organizers, 70 participants)")
    print(f"   - Events: {len(events_data)}")
    print(f"   - Bookings: {len(bookings_data)}")
    print("\nFiles updated:")
    print("   - backend/fixtures/02_partners.json")
    print("   - backend/fixtures/03_users.json")
    print("   - backend/fixtures/04_events.json")
    print("   - backend/fixtures/05_bookings.json")
    print("\nTo load fixtures, run:")
    print("   cd backend")
    print("   python manage.py loaddata 01_languages.json 02_partners.json 03_users.json 04_events.json 05_bookings.json")

if __name__ == "__main__":
    main()





