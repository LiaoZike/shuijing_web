import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Activity
from datetime import date

# Long URL (> 200 chars)
long_url = "https://example.com/" + "a" * 250

try:
    act = Activity.objects.create(
        title="Test Long URL",
        date=date.today(),
        location="Test Location",
        contact_name="Test Contact",
        contact_phone="123456789",
        link_url=long_url
    )
    print(f"Successfully created Activity with URL length: {len(act.link_url)}")
    act.delete()
except Exception as e:
    print(f"Failed to create Activity: {e}")
