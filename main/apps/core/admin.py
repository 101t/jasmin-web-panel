# -*- encoding: utf-8 -*-
from django.contrib import admin
from .models import FiltersModel, GroupsModel, UsersModel, HTTPccmModel, SMPPccmModel, MORoutersModel, MTRoutersModel

class FiltersModelAdmin(admin.ModelAdmin):
	list_display = ("type", "fid", "parameters",)

class GroupsModelAdmin(admin.ModelAdmin):
	list_display = ('gid', 'status',)

class UsersModelAdmin(admin.ModelAdmin):
	list_display = ("uid", "gid", "username", "password", "parameters",)

class HTTPccmModelAdmin(admin.ModelAdmin):
	list_display = ("cid", "url", "method",)

class SMPPccmModelAdmin(admin.ModelAdmin):
	list_display = ("cid", "parameters", "action",)

class MORoutersModelAdmin(admin.ModelAdmin):
	list_display = ("type", "order", "smppconnectors", "httpconnectors", "filters",)

class MTRoutersModelAdmin(admin.ModelAdmin):
	list_display = ("type", "order", "rate", "smppconnectors", "httpconnectors", "filters",)

admin.site.register(FiltersModel, FiltersModelAdmin)
admin.site.register(GroupsModel, GroupsModelAdmin)
admin.site.register(UsersModel, UsersModelAdmin)
admin.site.register(HTTPccmModel, HTTPccmModelAdmin)
admin.site.register(SMPPccmModel, SMPPccmModelAdmin)
admin.site.register(MORoutersModel, MORoutersModelAdmin)
admin.site.register(MTRoutersModel, MTRoutersModelAdmin)