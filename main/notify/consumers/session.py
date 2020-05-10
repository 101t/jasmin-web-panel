# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import asyncio
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = str('session_%s' % self.session_id)

        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data = json.dumps(
            dict(data='connected')
        ))

    # Receive data from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data['text'])['data']
        # Send data to room group
        await self.channel_layer.group_send(
            self.session_group_name,
            dict(
                type='data_handller',
                data=data,
            )
        )

    # Receive data from room group
    async def data_handller(self, event):
        data = event['data']
        # Send data to WebSocket
        await self.send(text_data=json.dumps(
            dict(data=data)
        ))

    async def disconnect(self, event):
        print("Disconnected : {} , Event {}".format(self.channel_name, event))
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )