#!/usr/bin/env bash
# build.sh

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Try to merge migrations if needed
python manage.py makemigrations --merge --no-input || true

# Apply database migrations
python manage.py migrate --no-input

# Create default Site object for django-allauth (if it doesn't exist)
python manage.py shell << END
from django.contrib.sites.models import Site
try:
    site = Site.objects.get(pk=1)
    site.domain = 'crimewatch-reporting-system.onrender.com'
    site.name = 'CrimeWatch Reporting System'
    site.save()
    print("Site configured successfully")
except Site.DoesNotExist:
    Site.objects.create(
        pk=1,
        domain='crimewatch-reporting-system.onrender.com',
        name='CrimeWatch Reporting System'
    )
    print("Site created successfully")
END

# Create superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin2').exists():
    user = User.objects.create_superuser('admin2', 'admin2@crimewatch.co.za', 'Halogenxtjail@11')
    print(f"Superuser 'admin2' created successfully")
    print("=" * 50)
    print("IMPORTANT: Change this password after first login!")
    print("Username: admin2")
    print("Password: Halogenxtjail@11")
    print("=" * 50)
else:
    print("Superuser 'admin' already exists")
END

echo "Build completed successfully!"