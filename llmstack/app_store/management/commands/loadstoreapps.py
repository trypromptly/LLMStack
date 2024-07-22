import os

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Loads initial data for the app store"

    def handle(self, *args, **options):
        """
        Loads apps from STORE_APPS_DIR. Updates existing apps if they exist.
        """
        from llmstack.app_store.apis import AppStoreAppViewSet
        from llmstack.app_store.models import AppStoreApp

        if settings.STORE_APPS_DIR:
            store_apps_dir = settings.STORE_APPS_DIR

            # Get all the yml files in the store apps directory
            for entry in store_apps_dir:
                yml_files = [
                    f for f in os.listdir(entry) if os.path.isfile(os.path.join(entry, f)) and f.endswith(".yml")
                ]

                for yml_file in yml_files:
                    with open(os.path.join(entry, yml_file), "r") as stream:
                        app_data = yaml.safe_load(stream)

                        # Check if icon is present in the app data. If it is a relative path, convert it to an absolute path
                        if "icon" in app_data:
                            icon = app_data["icon"]
                            if not icon.startswith("http"):
                                app_data["icon"] = os.path.join(entry, icon)

                        # Check if the app already exists and version is the same
                        app = AppStoreApp.objects.filter(slug=app_data["slug"]).first()
                        if app and app.version == app_data["version"]:
                            self.stdout.write(self.style.SUCCESS(f"Skipping app {app_data['slug']}"))
                            continue

                        try:
                            AppStoreAppViewSet.create_or_update(app_data, obj=app)

                            if app:
                                self.stdout.write(self.style.SUCCESS(f"Updated app {app_data['slug']}"))
                            else:
                                self.stdout.write(self.style.SUCCESS(f"Loaded app {app_data['slug']}"))
                        except Exception as e:
                            import traceback

                            print(traceback.format_exc())
                            self.stdout.write(self.style.ERROR(f"Error loading app {app_data['slug']}"))
                            self.stdout.write(self.style.ERROR(e))
