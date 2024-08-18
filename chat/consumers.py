from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from django.contrib.auth.models import User
from .models import Message

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.other_user = int(self.scope['url_route']['kwargs']['user_id'])
        self.room_group_name = f'chat_{min(self.user.id, self.other_user)}_{max(self.user.id, self.other_user)}'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # Save message to database
        try:
            receiver = User.objects.get(id=self.other_user)
            message_instance = Message.objects.create(sender=self.user, receiver=receiver, content=message)
        except Exception as e:
            print(f"Error saving message: {e}")
            return

        timestamp = message_instance.timestamp.strftime('%H:%M %p')

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_instance.content,
                'sender': self.user.username,
                'sender_id': self.user.id,
                'timestamp': timestamp,
                'last_message': message_instance.content,  # Include last message
                'last_message_timestamp': timestamp  # Include timestamp
            }
        )

    def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        sender_id = event['sender_id']
        timestamp = event['timestamp']
        last_message = event['last_message']
        last_message_timestamp = event['last_message_timestamp']

        # Send the message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'sender_id': sender_id,
            'timestamp': timestamp,
            'last_message': last_message,
            'last_message_timestamp': last_message_timestamp
        }))
