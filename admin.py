from django.contrib import admin
from models import *
class RoomAdmin(admin.ModelAdmin):
	list_display = ('room', 'bhavan','vacancy')
admin.site.register(bill)
admin.site.register(Room, RoomAdmin)
admin.site.register(Bhavan)
