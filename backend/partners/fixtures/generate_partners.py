import json
import random
from datetime import datetime
from pathlib import Path

NAMES = [
    "Café de la Bourse", "Le Botanique Bar", "La Guinguette du Parc",
    "Bar Louise", "Le Flagey", "Brasserie du Parc", "Chez Léon",
    "Le Châtelain", "Bar Toison d'Or", "La Porte de Namur",
    "Ixelles Café", "Schaerbeek Lounge", "Saint-Gilles Bar",
    "Anderlecht Corner", "Woluwe Pub", "Le Cinquantenaire",
    "Bar Central", "Café de l'Europe", "La Terrasse Etterbeek",
    "Bruxelles By Night", "Café du Sablon", "Matongé Bar",
    "La Grand Place", "Quartier Latin Café", "Uccle Lounge",
    "Le Parlement Bar", "Café des Halles", "Tour & Taxis Pub",
    "Bar Botanica", "Molenbeek Spot", "Bourse Corner",
    "Le Cinéma Café", "La Gare du Midi", "Brasserie Royale",
    "Café du Canal", "Place Jourdan Bar", "Laeken Lounge",
    "Café Louise 2", "Ixelles Spot", "Woluwe House",
    "Le Tram Bar", "Bruxelles Chill", "Le Studio Café",
    "Anderlecht Lounge", "Café du Parc", "Le Delta",
    "Saint-Josse Café", "Schaerbeek Bar", "Ixelles Rooftop",
    "Uccle Garden"
]

ADDRESSES = [
    "Rue du Midi", "Boulevard Botanique", "Avenue Louise", "Place Flagey",
    "Chaussée de Charleroi", "Rue de la Loi", "Boulevard Anspach",
    "Parc du Cinquantenaire", "Place Jourdan", "Chaussée de Wavre",
    "Boulevard Général Jacques", "Rue du Bailli", "Place Sainte-Catherine",
    "Rue Dansaert", "Chaussée d'Ixelles", "Place de Brouckère",
    "Rue Haute", "Boulevard du Jardin Botanique", "Rue Royale",
    "Chaussée de Waterloo"
]

CITIES = [
    "Bruxelles", "Ixelles", "Saint-Gilles", "Etterbeek", 
    "Schaerbeek", "Uccle", "Molenbeek", "Anderlecht", 
    "Woluwe", "Laeken", "Saint-Josse"
]

OUTPUT_FILE = Path(__file__).resolve().parent / "partners.json"

def generate_fixture(n=50):
    now = datetime.utcnow().isoformat() + "Z"  # timestamp UTC ISO 8601
    data = []

    for i in range(1, n + 1):
        name = random.choice(NAMES)
        address = f"{random.choice(ADDRESSES)} {random.randint(1, 250)}, 1000 Bruxelles"
        reputation = round(random.uniform(3.0, 5.0), 1)
        capacity = random.randint(10, 30)
        city = random.choice(CITIES)

        partner = {
            "model": "partners.partner",
            "pk": i,
            "fields": {
                "name": name,
                "address": address,
                "city": city,  # <── ajouté ici
                "reputation": reputation,
                "capacity": capacity,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
        }
        data.append(partner)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Fixture générée : {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_fixture(50)
