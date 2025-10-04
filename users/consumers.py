# users/consumers.py (최종 완성본)

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.db.models import Q
from .models import ChatMessage

# --- 개인별 실시간 알림을 처리하는 컨슈머 ---
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        # 자기 자신만의 개인 알림 그룹(예: notifications_39)에 접속
        self.group_name = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # 그룹으로부터 알림 메시지를 받았을 때 실행될 함수
    async def send_notification(self, event):
        # 받은 메시지(event)를 그대로 클라이언트(브라우저)에게 전달
        await self.send(text_data=json.dumps(event))

# --- 기존 채팅방 컨슈머 ---
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        partner_id = int(self.scope['url_route']['kwargs']['user2_id'])
        
        user1_id = self.user.id
        user2_id = partner_id
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        self.room_name = f'{user1_id}_{user2_id}'
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.mark_messages_as_read(partner_id)
        messages = await self.get_messages(partner_id)
        
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message['content'],
                'sender_username': message['sender__username']
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.user
        receiver_id = int(self.scope['url_route']['kwargs']['user2_id'])

        new_message = await self.save_message(sender, receiver_id, message)

        # 1. 채팅방에 있는 사람들에게 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'message': message, 'sender_username': sender.username}
        )

        # 2. 메시지 수신자의 '개인 알림 채널'로 알림 전송
        receiver_notification_group = f'notifications_{receiver_id}'
        await self.channel_layer.group_send(
            receiver_notification_group,
            {
                'type': 'send_notification',
                'notification_type': 'new_message',
                'sender_id': sender.id,
                'sender_name': sender.first_name,
                'sender_username': sender.username,
                'last_message': new_message.content,
                'timestamp': new_message.timestamp.isoformat(),
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender_username']
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_username': sender_username
        }))

    @database_sync_to_async
    def save_message(self, sender, receiver_id, message):
        receiver = User.objects.get(id=receiver_id)
        new_message = ChatMessage.objects.create(sender=sender, receiver=receiver, content=message)
        return new_message

    @database_sync_to_async
    def get_messages(self, partner_id):
        messages = ChatMessage.objects.filter(
            (Q(sender=self.user.id, receiver=partner_id) | Q(sender=partner_id, receiver=self.user.id))
        ).order_by('timestamp').values('content', 'sender__username')
        return list(messages)

    @database_sync_to_async
    def mark_messages_as_read(self, partner_id):
        updated_count = ChatMessage.objects.filter(sender_id=partner_id, receiver=self.user, is_read=False).update(is_read=True)
        print(f"--- 🕵️ {updated_count}개의 메시지를 '읽음'으로 변경했습니다. ---")