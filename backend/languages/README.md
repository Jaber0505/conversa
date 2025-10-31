# Module Languages

## Vue d'ensemble

Données de référence pour les langues disponibles (ISO 639-1).

## Caractéristiques

- **Code ISO** : Code langue 2 lettres (ex: `fr`, `en`, `nl`)
- **Labels multilingues** : Traductions FR/EN/NL
- **Ordre d'affichage** : `sort_order` pour tri custom
- **Activation** : `is_active` pour activer/désactiver langues

## Structure

```
languages/
├── models.py          # Language (code, labels, is_active)
├── serializers.py     # LanguageSerializer
├── views.py           # LanguageViewSet (read-only)
├── admin.py
└── tests/
    ├── test_models.py
    ├── test_serializers.py
    └── test_views.py
```

## Modèle

### Language
- `code` : Code ISO 639-1 (unique, 2 lettres)
- `label_fr`, `label_en`, `label_nl` : Traductions
- `is_active` : Langue active/inactive
- `sort_order` : Ordre d'affichage (défaut: 0)

### Méthode : `get_label(locale)`

Retourne le label dans la langue demandée :

```python
french = Language.objects.get(code='fr')
french.get_label('en')  # "French"
french.get_label('fr')  # "Français"
french.get_label('nl')  # "Frans"
french.get_label('xx')  # "Français" (fallback FR)
```

## Utilisation

### Créer une langue

```python
Language.objects.create(
    code="fr",
    label_fr="Français",
    label_en="French",
    label_nl="Frans",
    is_active=True,
    sort_order=1
)
```

### Lister langues actives

```python
active_languages = Language.objects.filter(is_active=True).order_by('sort_order')
```

## Tests

```bash
python manage.py test languages
```

**Coverage** : 9 tests (modèle, serializers, views)
