from django.conf import settings
from django.contrib import admin

admin.ModelAdmin.list_per_page = settings.LIST_PER_PAGE
admin.ModelAdmin.list_max_show_all = 0

# from me_live.tasks import load_spinning_wheel_game
# load_spinning_wheel_game.delay()
