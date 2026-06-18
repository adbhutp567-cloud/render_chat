from django.contrib import admin
from .models import ChatGroup, Groupmessage, Reaction

admin.site.register(ChatGroup)
admin.site.register(Groupmessage)
admin.site.register(Reaction)
