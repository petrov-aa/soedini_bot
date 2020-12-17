from django.contrib import admin

from .models import Chat, Session, Photo, ModeLog

admin.site.register(Chat)
admin.site.register(Session)
admin.site.register(Photo)
admin.site.register(ModeLog)
