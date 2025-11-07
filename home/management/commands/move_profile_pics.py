from django.core.management.base import BaseCommand
from django.conf import settings
import os
from home.models import Profile

class Command(BaseCommand):
    help = 'Move existing profile images from MEDIA_ROOT/(profile_pics|profile_pictures) to home/static/profile_pictures and update Profile.avatar paths'

    def handle(self, *args, **options):
        src_dirs = [
            os.path.join(settings.MEDIA_ROOT, 'profile_pics'),
            os.path.join(settings.MEDIA_ROOT, 'profile_pictures'),
        ]
        target_dir = os.path.join(settings.BASE_DIR, 'home', 'static', 'profile_pictures')
        os.makedirs(target_dir, exist_ok=True)
        moved = 0

        for profile in Profile.objects.all():
            if not profile.avatar:
                continue
            name = getattr(profile.avatar, 'name', '')
            if not name:
                continue
            # normalize name and check if it resides in one of the source dirs
            if name.startswith('profile_pics/') or name.startswith('profile_pictures/'):
                filename = os.path.basename(name)
                # locate the existing file in media
                src_path = None
                for d in src_dirs:
                    candidate = os.path.join(d, filename)
                    if os.path.exists(candidate):
                        src_path = candidate
                        break
                if not src_path:
                    self.stdout.write(self.style.WARNING(f'Could not find source file for profile {profile.pk}: {name}'))
                    continue
                dst_path = os.path.join(target_dir, filename)
                try:
                    os.replace(src_path, dst_path)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to move {src_path} -> {dst_path}: {e}'))
                    continue
                # update DB to point to new storage-relative name (we store filename)
                profile.avatar.name = filename
                profile.save(update_fields=['avatar'])
                moved += 1
                self.stdout.write(self.style.SUCCESS(f'Moved {src_path} -> {dst_path} for profile {profile.pk}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Files moved: {moved}'))
