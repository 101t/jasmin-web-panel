
from main.apps.core.models import UsersModel, GroupsModel
from django.contrib.auth.models import User

class UserManager(object):
	def __init__(self):
		pass
	def add(self, data):
		uid = data["uid"]
		gid = data["gid"]
		username = data["username"]
		password = data["password"]
		g, created = GroupsModel.objects.get_or_create(gid=gid,)
		user = User.objects.create_user(username=username, email=None, password=password)
		users_model = UsersModel.objects.create(uid=uid, gid=g, username=username, password=password, user=user)
	def update(self, data, uid):
		uid = data["uid"]
		gid = data["gid"]
		username = data["username"]
		password = data.get("password", "")
		g, created = GroupsModel.objects.get_or_create(gid=gid,)
		users_model = UsersModel.objects.filter(uid=uid).first()
		if users_model:
			user = User.objects.filter(username=users_model.user.username).first()
			users_model.uid = uid
			users_model.gid = g
			users_model.username = username
			if len(password) > 0:
				users_model.password = password
			users_model.save()
			if user:
				user.username = username
				if len(password) > 0:
					user.set_password(password)
				user.save()

	def delete(self, uid):
		users_model = UsersModel.objects.filter(uid=uid).first()
		if users_model:
			user = User.objects.filter(username=users_model.user.username).first()
			if user:
				user.delete()
