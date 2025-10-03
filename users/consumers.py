# users/consumers.py (최종 수정본)

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.db.models import Q
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        # 1. URL에서 가져온 원본 상대방 ID를 별도의 변수에 저장
        partner_id = int(self.scope['url_route']['kwargs']['user2_id'])
        
        # 2. 방 이름을 만들기 위해 ID 정렬
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

        # 3. 정렬 전의 원본 상대방 ID(partner_id)를 사용
        await self.mark_messages_as_read(partner_id)
        messages = await self.get_messages(partner_id)
        
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message['content'],
                'sender_username': message['sender__username']
            }))

    # ... (disconnect, receive, chat_message, save_message 함수는 동일) ...
    
    @database_sync_to_async
    def get_messages(self, partner_id): # 인자 이름 통일
        messages = ChatMessage.objects.filter(
            (Q(sender=self.user.id, receiver=partner_id) | Q(sender=partner_id, receiver=self.user.id))
        ).order_by('timestamp').values('content', 'sender__username')
        return list(messages)

    @database_sync_to_async
    def mark_messages_as_read(self, partner_id): # 인자 이름 통일
        print(f"--- 🕵️ '읽음' 처리 시작: 받는사람(나)={self.user.id}, 보낸사람={partner_id} ---")
        updated_count = ChatMessage.objects.filter(sender_id=partner_id, receiver=self.user, is_read=False).update(is_read=True)
        print(f"   - >> {updated_count}개의 메시지를 '읽음'으로 변경했습니다.")