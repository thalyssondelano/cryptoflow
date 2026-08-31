from django.contrib import admin
from .models import CustomUser, Wallet
from django.contrib.auth.admin import UserAdmino 

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Wallet)