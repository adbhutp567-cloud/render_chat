from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from .models import ChatGroup, Groupmessage, VideoCall
from django.contrib.auth import get_user_model
from django.utils import timezone
import json


User = get_user_model()

def parse_private_chat_group_name(group_name):
    parts = group_name.split('-')
    if len(parts) != 3 or parts[0] != 'private':
        return None
    try:
        return int(parts[1]), int(parts[2])
    except ValueError:
        return None


def get_private_partner_from_group(group_name, current_user_id):
    parsed = parse_private_chat_group_name(group_name)
    if not parsed:
        return None
    user1, user2 = parsed
    if current_user_id == user1:
        return User.objects.filter(id=user2).first()
    if current_user_id == user2:
        return User.objects.filter(id=user1).first()
    return None


def is_blocked(user, other):
    return other and user.blocked_users.filter(id=other.id).exists()


class ChatroomConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']

        if self.chatroom_name == 'uptti' or self.chatroom_name.startswith('private-'):
            self.chatroom, _ = ChatGroup.objects.get_or_create(group_name=self.chatroom_name)
        else:
            self.chatroom = ChatGroup.objects.filter(group_name=self.chatroom_name).first()
            if self.chatroom is None:
                return self.close()

        if not self.user.is_authenticated:
            return self.close()

        if self.chatroom_name.startswith('private-'):
            partner = get_private_partner_from_group(self.chatroom_name, self.user.id)
            if not partner:
                return self.close()
        elif self.chatroom_name != 'uptti' and not self.chatroom.is_member(self.user):
            return self.close()

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        # Subscribe to personal notifications for private messages
        if self.user.is_authenticated:
            notification_group = f'notifications-{self.user.id}'
            async_to_sync(self.channel_layer.group_add)(
                notification_group, self.channel_name
            )

        # add and update online users
        if self.user.is_authenticated and self.user not in self.chatroom.users_name.all():
            self.chatroom.users_name.add(self.user)
            self.update_online_count()

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )

        # Unsubscribe from personal notifications
        if self.user.is_authenticated:
            notification_group = f'notifications-{self.user.id}'
            async_to_sync(self.channel_layer.group_discard)(
                notification_group,
                self.channel_name
            )

        # remove and update online users
        if self.user.is_authenticated and self.user in self.chatroom.users_name.all():
            self.chatroom.users_name.remove(self.user)
            self.update_online_count()

    def receive(self, text_data):
        print(f"[CONSUMER] Received data: {text_data[:200]}")
        try:
            payload = json.loads(text_data)
        except ValueError as e:
            print(f"[CONSUMER] JSON parsing error: {e}")
            return
        
        print(f"[CONSUMER] Parsed payload: {payload}")
        
        # Handle video call events
        call_type = payload.get('type')
        
        if call_type == 'call_initiation':
            self.handle_call_initiation(payload)
        elif call_type == 'call_answer':
            self.handle_call_answer(payload)
        elif call_type == 'call_decline':
            self.handle_call_decline(payload)
        elif call_type == 'ice_candidate':
            self.handle_ice_candidate(payload)
        elif call_type == 'call_end':
            self.handle_call_end(payload)
        elif call_type == 'receipt':
            self.handle_receipt(payload)
        else:
            # default: handle chat messages
            if self.chatroom_name.startswith('private-'):
                partner = get_private_partner_from_group(self.chatroom_name, self.user.id)
                if partner and (is_blocked(self.user, partner) or is_blocked(partner, self.user)):
                    print(f"[CONSUMER] Blocked message ignored between {self.user.username} and {partner.username}")
                    return

            body = str(payload.get('body', '')).strip()
            reply_to = payload.get('reply_to')
            reply_to_id = None
            if reply_to:
                try:
                    reply_to_id = int(reply_to)
                except (TypeError, ValueError):
                    reply_to_id = None

            print(f"[CONSUMER] Chat message - body: {body[:50]}, reply_to_id: {reply_to_id}, authenticated: {self.user.is_authenticated}")
            
            if not self.user.is_authenticated or not body:
                print(f"[CONSUMER] Message rejected - auth: {self.user.is_authenticated}, body empty: {not body}")
                return

            print(f"[CONSUMER] Creating message for user {self.user.username}")
            message = Groupmessage.objects.create(
                body=body,
                author=self.user,
                group=self.chatroom,
                reply_to_id=reply_to_id,
            )
            
            print(f"[CONSUMER] Message created with ID: {message.id}")

            html = render_to_string(
                'a_rtchat/partials/chat_message_p.html',
                {'message': message, 'user': self.user}
            )

            # Send message to sender immediately, then broadcast to everyone else in the room
            self.send(text_data=html)
            async_to_sync(self.channel_layer.group_send)(
                self.chatroom_name,
                {
                    'type': 'message_handler',
                    'message_id': message.id,
                    'sender_channel': self.channel_name,
                }
            )

            # Send notification for private messages
            if self.chatroom_name.startswith('private-'):
                partner = get_private_partner_from_group(self.chatroom_name, self.user.id)
                if partner:
                    # Send notification to partner if they're not currently in chat
                    async_to_sync(self.channel_layer.group_send)(
                        f'notifications-{partner.id}',
                        {
                            'type': 'message_notification',
                            'sender_name': self.user.get_full_name() or self.user.username,
                            'sender_username': self.user.username,
                            'message_preview': body[:50],
                            'sender_avatar': self.user.avatar,
                            'chatroom_name': self.chatroom_name,
                        }
                    )

    def handle_call_initiation(self, payload):
        """Handle incoming video call"""
        receiver_username = payload.get('receiver_username')
        offer = payload.get('offer')
        
        if not receiver_username or not offer:
            return
        
        try:
            receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            self.send(text_data=json.dumps({'type': 'error', 'message': 'Receiver not found'}))
            return

        if is_blocked(self.user, receiver) or is_blocked(receiver, self.user):
            print(f"[CONSUMER] Blocked call initiation ignored between {self.user.username} and {receiver_username}")
            return

        # Create video call record
        call = VideoCall.objects.create(
            caller=self.user,
            receiver=receiver,
            group=self.chatroom,
            status='ringing'
        )
        
        # Send call notification to receiver
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'call_initiation_handler',
                'caller_username': self.user.username,
                'caller_id': self.user.id,
                'receiver_username': receiver_username,
                'offer': offer,
                'call_id': call.id,
            }
        )

    def handle_call_answer(self, payload):
        """Handle call accepted"""
        call_id = payload.get('call_id')
        answer = payload.get('answer')
        
        if not call_id or not answer:
            return
        
        try:
            call = VideoCall.objects.get(id=call_id)
            call.status = 'accepted'
            call.answered_at = timezone.now()
            call.save()
        except VideoCall.DoesNotExist:
            return
        
        # Send answer to caller
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'call_answer_handler',
                'call_id': call_id,
                'answer': answer,
                'receiver_username': self.user.username,
            }
        )

    def handle_call_decline(self, payload):
        """Handle call declined"""
        call_id = payload.get('call_id')
        
        if not call_id:
            return
        
        try:
            call = VideoCall.objects.get(id=call_id)
            call.status = 'declined'
            call.ended_at = timezone.now()
            call.save()
        except VideoCall.DoesNotExist:
            return
        
        # Notify both users
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'call_decline_handler',
                'call_id': call_id,
            }
        )

    def handle_ice_candidate(self, payload):
        """Handle ICE candidate"""
        call_id = payload.get('call_id')
        candidate = payload.get('candidate')
        
        if not call_id or not candidate:
            return
        
        # Broadcast ICE candidate to other user in the call
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'ice_candidate_handler',
                'call_id': call_id,
                'candidate': candidate,
                'from_user': self.user.username,
            }
        )

    def handle_call_end(self, payload):
        """Handle call ended"""
        call_id = payload.get('call_id')
        
        if not call_id:
            return
        
        try:
            call = VideoCall.objects.get(id=call_id)
            if call.answered_at:
                duration = (timezone.now() - call.answered_at).total_seconds()
                call.call_duration = int(duration)
            call.status = 'completed'
            call.ended_at = timezone.now()
            call.save()
        except VideoCall.DoesNotExist:
            return
        
        # Notify both users
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            {
                'type': 'call_end_handler',
                'call_id': call_id,
            }
        )

    def handle_receipt(self, payload):
        message_id = payload.get('message_id')
        receipt_type = payload.get('receipt_type')
        if not message_id or receipt_type not in ('delivered', 'read'):
            return

        try:
            message = Groupmessage.objects.get(id=message_id)
        except Groupmessage.DoesNotExist:
            return

        if message.author == self.user:
            return

        updated = False
        if receipt_type == 'delivered' and not message.delivered:
            message.delivered = True
            updated = True
        if receipt_type == 'read' and not message.read:
            message.read = True
            updated = True
        if updated:
            message.save(update_fields=['delivered', 'read'])
            async_to_sync(self.channel_layer.group_send)(
                self.chatroom_name,
                {
                    'type': 'message_update_handler',
                    'message_id': message.id,
                }
            )

    def message_handler(self, event):
        if event.get('sender_channel') == self.channel_name:
            print(f"[MESSAGE_HANDLER] Skipping sender channel for {self.user.username}")
            return

        message_id = event['message_id']
        print(f"[MESSAGE_HANDLER] Delivering message {message_id} to user {self.user.username}")
        try:
            message = Groupmessage.objects.select_related('author', 'reply_to').prefetch_related('reactions').get(id=message_id)
            html = render_to_string(
                'a_rtchat/partials/chat_message_p.html',
                {'message': message, 'user': self.user}
            )
            print(f"[MESSAGE_HANDLER] Sending HTML ({len(html)} chars) to {self.user.username}")
            self.send(text_data=html)
        except Exception as e:
            print(f"[MESSAGE_HANDLER] Error: {e}")
    
    def call_initiation_handler(self, event):
        """Send call initiation to receiver"""
        # Only send to the receiver
        if event.get('receiver_username') == self.user.username or event.get('caller_id') == self.user.id:
            self.send(text_data=json.dumps({
                'type': 'call_initiation',
                'caller_username': event.get('caller_username'),
                'offer': event.get('offer'),
                'call_id': event.get('call_id'),
            }))

    def call_answer_handler(self, event):
        """Send answer to caller"""
        self.send(text_data=json.dumps({
            'type': 'call_answer',
            'call_id': event.get('call_id'),
            'answer': event.get('answer'),
            'receiver_username': event.get('receiver_username'),
        }))

    def call_decline_handler(self, event):
        """Notify call declined"""
        self.send(text_data=json.dumps({
            'type': 'call_decline',
            'call_id': event.get('call_id'),
        }))

    def ice_candidate_handler(self, event):
        """Send ICE candidate"""
        self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'call_id': event.get('call_id'),
            'candidate': event.get('candidate'),
            'from_user': event.get('from_user'),
        }))

    def call_end_handler(self, event):
        """Notify call ended"""
        self.send(text_data=json.dumps({
            'type': 'call_end',
            'call_id': event.get('call_id'),
        }))

    def delete_message_handler(self, event):
        message_id = event['message_id']
        html = f'<div hx-swap-oob="delete" hx-target="#message-{message_id}"></div>'
        self.send(text_data=html)

    def message_update_handler(self, event):
        """Send an out-of-band replacement for a single message when it changes (pinned/unpinned)."""
        message_id = event.get('message_id')
        try:
            message = Groupmessage.objects.select_related('author', 'reply_to').prefetch_related('reactions').get(id=message_id)
            html = render_to_string('a_rtchat/partials/chat_message_oob.html', {'message': message, 'user': self.user})
            self.send(text_data=html)
        except Exception as e:
            print(f"[MESSAGE_UPDATE_HANDLER] Error: {e}")

    def update_online_count(self):
        online_count = self.chatroom.users_name.count()

        event = {
            'type': 'online_count_handler',
            'online_count': online_count
        }
        async_to_sync(self.channel_layer.group_send)(self.chatroom_name, event)

    def online_count_handler(self, event):
        online_count = event['online_count']

        html = render_to_string("a_rtchat/partials/online_count.html", {'online_count': online_count})
        self.send(text_data=html)

    def message_notification(self, event):
        """Send notification for incoming private messages"""
        notification = {
            'type': 'notification',
            'sender_name': event.get('sender_name'),
            'sender_username': event.get('sender_username'),
            'message_preview': event.get('message_preview'),
            'sender_avatar': event.get('sender_avatar'),
            'chatroom_name': event.get('chatroom_name'),
        }
        self.send(text_data=json.dumps(notification))
