# build.sh
#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate --no-input

# Create default Site object for django-allauth (if it doesn't exist)
python manage.py shell << END
from django.contrib.sites.models import Site
try:
    site = Site.objects.get(pk=1)
    site.domain = 'crimewatch-reporting-system.onrender.com'
    site.name = 'Crime Watch Reporting System'
    site.save()
except Site.DoesNotExist:
    Site.objects.create(
        pk=1,
        domain='crimewatch-reporting-system.onrender.com',
        name='Crime Watch Reporting System'
    )
print("Site configured successfully")
END

echo "Build completed successfully!"