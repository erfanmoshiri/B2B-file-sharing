import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "final_project.settings")
django.setup()
# from final_project import settings
# settings.configure()

from bit_torrent.models import Tracker


if __name__ == '__main__':
    print('hi')
    tracker = Tracker()
    tracker.listen_to_requests()
