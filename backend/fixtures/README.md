# Django Fixtures

This directory contains test/development data for the Conversa application.

## Files

The fixtures are numbered to ensure correct loading order (respecting dependencies):

1. **01_languages.json** (12 languages: fr, en, es, nl, de, it, pt, ar, tr, ru, zh, ja)
   - No dependencies
   - Required by: users, events

2. **02_partners.json** (55 partner venues in Brussels)
   - No dependencies
   - Required by: events

3. **03_users.json** (Development users with various profiles)
   - Depends on: languages
   - Required by: events, bookings

4. **04_events.json** (Sample language exchange events)
   - Depends on: users, languages, partners
   - Required by: bookings

## Loading Fixtures

### Load all fixtures (correct order):
```bash
python manage.py loaddata 01_languages 02_partners 03_users 04_events
```

### Load specific fixtures:
```bash
# Languages only
python manage.py loaddata 01_languages

# Partners only  
python manage.py loaddata 02_partners

# Users (requires languages first)
python manage.py loaddata 01_languages 03_users

# Events (requires all)
python manage.py loaddata 01_languages 02_partners 03_users 04_events
```

### Docker:
```bash
docker exec conversa-backend python manage.py loaddata 01_languages 02_partners 03_users 04_events
```

## Fixture Generation

Fixtures can be generated from the database:

```bash
# Export languages
python manage.py dumpdata languages.Language --indent=2 > backend/fixtures/01_languages.json

# Export partners
python manage.py dumpdata partners.Partner --indent=2 > backend/fixtures/02_partners.json

# Export users (exclude sensitive data)
python manage.py dumpdata users.User --indent=2 > backend/fixtures/03_users.json

# Export events
python manage.py dumpdata events.Event --indent=2 > backend/fixtures/04_events.json
```

## Notes

- **Old fixture locations removed**: Fixtures were previously scattered in app-specific directories (`languages/fixtures/`, `partners/fixtures/`, etc.). All fixtures are now centralized here.

- **Dependency order matters**: Always load fixtures in numerical order to avoid foreign key errors.

- **Test isolation**: Django tests automatically use a separate test database and don't require manual fixture loading.

- **Production**: These fixtures are for development/testing only. Production data should be migrated separately.
