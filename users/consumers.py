import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    # WebSocket 연결이 처음 맺어질 때 실행
    async def connect(self):
        # URL 경로에서 'room_name'을 가져옴 (예: /ws/chat/room123/ -> room123)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # 채팅 그룹(채널)에 현재 사용자를 추가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # WebSocket 연결을 수락
        await self.accept()

    # WebSocket 연결이 끊어질 때 실행
    async def disconnect(self, close_code):
        # 채팅 그룹(채널)에서 현재 사용자를 제거
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 클라이언트로부터 메시지를 받았을 때 실행
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 채팅 그룹(채널)에 있는 모든 사람에게 메시지를 다시 보냄 (broadcast)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message', # group_send를 받아서 실행할 함수 이름
                'message': message
            }
        )

    # 위 group_send에서 메시지를 받았을 때, 각 클라이언트가 실행할 함수
    async def chat_message(self, event):
        message = event['message']

        # WebSocket을 통해 클라이언트에게 메시지를 JSON 형식으로 보냄
        await self.send(text_data=json.dumps({
            'message': message
        }))