#!/bin/sh

set -e

host="$1"
shift

echo "⏳ Attente de la base de données à l'adresse $host..."

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  >&2 echo "🚫 PostgreSQL indisponible - attente..."
  sleep 1
done

>&2 echo "✅ PostgreSQL est prêt"
exec "$@"
