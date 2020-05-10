from main.users.models import User

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer

class BroadcastConsumer(JsonWebsocketConsumer):
	groups = ["broadcast"]
	def get_data(self, status, cmd="state", **kwargs):
		return dict(
			type="send.all",
			sender=self.user.username,
			role=self.user.role,
			status=status,
			cmd=cmd,
			**kwargs,
		)
	def connect(self):
		self.user = self.scope["user"]
		if self.user.is_anonymous:
			self.close()
		else:
			self.accept()
			async_to_sync(self.channel_layer.group_add)("broadcast", self.channel_name)
			async_to_sync(self.channel_layer.group_send)("broadcast", self.get_data(status="online"))
	def disconnect(self, close_code):
		async_to_sync(self.channel_layer.group_send)("broadcast", self.get_data(status="offline"))
		async_to_sync(self.channel_layer.group_discard)("broadcast", self.channel_name)
	def send_all(self, event):
		self.send_json(event)