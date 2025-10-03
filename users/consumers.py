import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage
from django.db.models import Q

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 두 사용자의 ID를 기반으로 고유한 채팅방 이름을 생성 (ID가 낮은 순으로)
        user1_id = self.scope['user'].id
        user2_id = int(self.scope['url_route']['kwargs']['user2_id'])
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        self.room_name = f'{user1_id}_{user2_id}'
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # --- 과거 메시지 불러와서 전송하는 로직 추가 ---
        messages = await self.get_messages()
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message['content'],
                'sender_username': message['sender__username']
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']
        receiver_id = int(self.scope['url_route']['kwargs']['user2_id'])

        # 데이터베이스에 메시지 저장
        await self.save_message(sender, receiver_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_username': sender.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender_username']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_username': sender_username
        }))

    # 데이터베이스에 메시지를 저장하는 비동기 함수
    @database_sync_to_async
    def save_message(self, sender, receiver_id, message):
        receiver = User.objects.get(id=receiver_id)
        ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=message
        )

    @database_sync_to_async
    def get_messages(self):
        messages = ChatMessage.objects.filter(
            Q(sender=self.scope['user'], receiver_id=self.scope['url_route']['kwargs']['user2_id']) |
            Q(sender_id=self.scope['url_route']['kwargs']['user2_id'], receiver=self.scope['user'])
        ).order_by('timestamp').values('content', 'sender__username')
        return list(messages)