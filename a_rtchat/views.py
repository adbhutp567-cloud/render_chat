from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .forms import ChatmessageCreateFrom, CreateGroupForm
from .models import ChatGroup, Groupmessage, Reaction, VideoCall


def broadcast_message(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        message.group.group_name,
        {
            'type': 'message_handler',
            'message_id': message.id,
        }
    )


def get_private_chat_group_name(user1, user2):
    ids = sorted([str(user1.id), str(user2.id)])
    return f'private-{ids[0]}-{ids[1]}'


def parse_private_chat_group_name(group_name):
    parts = group_name.split('-')
    if len(parts) != 3 or parts[0] != 'private':
        return None
    try:
        return int(parts[1]), int(parts[2])
    except ValueError:
        return None


def get_private_chats_for_user(user):
    User = get_user_model()
    private_chats = []
    groups = ChatGroup.objects.filter(group_name__startswith='private-')
    for group in groups:
        parsed = parse_private_chat_group_name(group.group_name)
        if not parsed or user.id not in parsed:
            continue
        partner_id = parsed[1] if parsed[0] == user.id else parsed[0]
        try:
            partner = User.objects.get(id=partner_id)
        except User.DoesNotExist:
            continue
        private_chats.append({
            'chatroom_name': group.group_name,
            'user': partner,
            'url': reverse('private-chat', args=[partner.username]),
        })
    return private_chats


def get_group_chats_for_user(user):
    return ChatGroup.objects.filter(members=user).exclude(group_name='uptti').order_by('group_name')


def get_recent_statuses(user):
    User = get_user_model()
    recent_statuses = []
    groups = ChatGroup.objects.filter(group_name__startswith='private-')
    for group in groups:
        parsed = parse_private_chat_group_name(group.group_name)
        if not parsed or user.id not in parsed:
            continue
        partner_id = parsed[1] if parsed[0] == user.id else parsed[0]
        try:
            partner = User.objects.get(id=partner_id)
        except User.DoesNotExist:
            continue
        if partner.status_active:
            recent_statuses.append({
                'user': partner,
                'url': reverse('private-chat', args=[partner.username]),
            })
    return recent_statuses


def render_chat_page(request, chat_group, chatroom_title=None, other_user=None, block_status=None):
    chat_messages = chat_group.chat_messages.select_related('author', 'reply_to').prefetch_related('reactions')[:25]
    form = ChatmessageCreateFrom()
    private_chats = get_private_chats_for_user(request.user)
    group_chats = get_group_chats_for_user(request.user)
    recent_statuses = get_recent_statuses(request.user)

    if chatroom_title is None:
        chatroom_title = 'Group Chat' if chat_group.group_name == 'uptti' else chat_group.display_name()

    return render(request, 'a_rtchat/chat.html', {
        'chat_messages': chat_messages,
        'form': form,
        'online_count': chat_group.users_name.count(),
        'chatroom_name': chat_group.group_name,
        'chatroom_title': chatroom_title,
        'private_chats': private_chats,
        'group_chats': group_chats,
        'recent_statuses': recent_statuses,
        'group': chat_group,
        'is_group_admin': chat_group.is_admin(request.user),
        'is_group_owner': chat_group.owner == request.user,
        'private_partner': other_user,
        'block_status': block_status or {},
    })


@login_required
def chat_view(request, chatroom_name='uptti', chatroom_title=None, other_user=None, block_status=None):
    chat_group, _ = ChatGroup.objects.get_or_create(group_name=chatroom_name)
    return render_chat_page(request, chat_group, chatroom_title, other_user, block_status)


@login_required
def private_chat_view(request, username):
    if request.user.username == username:
        return redirect('home')

    User = get_user_model()
    other_user = get_object_or_404(User, username=username)
    group_name = get_private_chat_group_name(request.user, other_user)
    chat_group, _ = ChatGroup.objects.get_or_create(group_name=group_name)

    chat_group.users_name.add(request.user)
    chat_group.users_name.add(other_user)

    block_status = {
        'user_has_blocked': request.user.blocked_users.filter(id=other_user.id).exists(),
        'other_has_blocked': other_user.blocked_users.filter(id=request.user.id).exists(),
    }

    return render_chat_page(
        request,
        chat_group,
        chatroom_title=f'Chat with {other_user.get_full_name() or other_user.username}',
        other_user=other_user,
        block_status=block_status
    )


@login_required
def block_user(request, username):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    if request.user.username == username:
        return HttpResponseBadRequest('Cannot block yourself')

    User = get_user_model()
    other_user = get_object_or_404(User, username=username)
    request.user.blocked_users.add(other_user)
    return redirect('private-chat', username=other_user.username)


@login_required
def unblock_user(request, username):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    User = get_user_model()
    other_user = get_object_or_404(User, username=username)
    request.user.blocked_users.remove(other_user)
    return redirect('private-chat', username=other_user.username)


@login_required
def start_private_chat(request):
    username = request.GET.get('username', '').strip()
    if not username:
        messages.error(request, 'Please enter a username to start a personal chat.')
        return redirect('home')

    if username == request.user.username:
        messages.error(request, 'You cannot start a private chat with yourself.')
        return redirect('home')

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'No user found with that username.')
        return redirect('home')

    return redirect('private-chat', username=user.username)


@login_required
def create_group(request):
    if request.method != 'POST':
        return redirect('home')

    form = CreateGroupForm(request.POST)
    if form.is_valid():
        chat_group = form.save(commit=False)
        chat_group.owner = request.user
        if not chat_group.title:
            chat_group.title = chat_group.group_name
        chat_group.save()
        chat_group.admins.add(request.user)
        chat_group.members.add(request.user)
        chat_group.users_name.add(request.user)
        messages.success(request, f'Group "{chat_group.display_name()}" created successfully.')
        return redirect('group-chat', chatroom_name=chat_group.group_name)

    for error_list in form.errors.values():
        for error in error_list:
            messages.error(request, error)
    return redirect('home')


@login_required
def group_chat_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if chat_group.group_name != 'uptti' and not chat_group.is_member(request.user):
        messages.error(request, 'You are not a member of that group.')
        return redirect('home')
    return render_chat_page(request, chat_group)


@login_required
def leave_group(request, chatroom_name):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if group.group_name == 'uptti':
        return HttpResponseBadRequest('Cannot leave the default group')

    if not group.is_member(request.user):
        return redirect('home')

    is_owner = group.owner == request.user
    group.members.remove(request.user)
    group.admins.remove(request.user)
    group.users_name.remove(request.user)

    if is_owner:
        new_owner = group.admins.first() or group.members.first()
        group.owner = new_owner
        group.save()

    if group.members.count() == 0:
        group.delete()
        messages.success(request, 'Group deleted because it no longer has members.')
        return redirect('home')

    messages.success(request, f'You left {group.display_name()}.')
    return redirect('home')


@login_required
def add_group_member(request, chatroom_name):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if not group.is_admin(request.user):
        return HttpResponseBadRequest('Unauthorized')

    username = request.POST.get('username', '').strip()
    if not username:
        messages.error(request, 'Please enter a username to add.')
        return redirect('group-chat', chatroom_name=group.group_name)

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('group-chat', chatroom_name=group.group_name)

    if group.is_member(user):
        messages.info(request, f'{user.username} is already a member of this group.')
        return redirect('group-chat', chatroom_name=group.group_name)

    group.members.add(user)
    messages.success(request, f'{user.username} was added to {group.display_name()}.')
    return redirect('group-chat', chatroom_name=group.group_name)


@login_required
def delete_group(request, chatroom_name):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if group.group_name == 'uptti' or not group.is_admin(request.user):
        return HttpResponseBadRequest('Unauthorized')

    group.delete()
    messages.success(request, 'Group deleted successfully.')
    return redirect('home')


@login_required
def chat_file_upload(request):
    if request.method != 'POST':
        return redirect('home')

    form = ChatmessageCreateFrom(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest('Invalid file upload')

    chatroom_name = request.POST.get('chatroom_name', 'uptti')
    if chatroom_name.startswith('private-'):
        parsed = parse_private_chat_group_name(chatroom_name)
        if parsed:
            user1_id, user2_id = parsed
            other_user_id = user1_id if user2_id == request.user.id else user2_id
            other_user = User.objects.filter(id=other_user_id).first()
            if other_user and (request.user.blocked_users.filter(id=other_user.id).exists() or other_user.blocked_users.filter(id=request.user.id).exists()):
                return HttpResponseBadRequest('You cannot upload files in a blocked private chat.')

    chat_group, _ = ChatGroup.objects.get_or_create(group_name=chatroom_name)
    message = form.save(commit=False)
    message.author = request.user
    message.group = chat_group
    reply_to_id = request.POST.get('reply_to')
    if reply_to_id:
        try:
            message.reply_to_id = int(reply_to_id)
        except (TypeError, ValueError):
            message.reply_to = None

    message.save()
    broadcast_message(message)

    return render(request, 'a_rtchat/partials/chat_message_p.html', {'message': message, 'user': request.user})


@login_required
def chat_message_react(request, message_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid reaction request')

    emoji = request.POST.get('emoji')
    if not emoji:
        return HttpResponseBadRequest('Missing emoji')

    message = get_object_or_404(Groupmessage, id=message_id)
    reaction, created = Reaction.objects.get_or_create(message=message, user=request.user, emoji=emoji)
    if not created:
        reaction.delete()

    # Broadcast the updated message to all connected chat participants so reactions appear in real time.
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        message.group.group_name,
        {
            'type': 'message_update_handler',
            'message_id': message.id,
        }
    )

    return render(request, 'a_rtchat/partials/reaction_summary.html', {'message': message})


@login_required
def chat_message_unsend(request, message_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid unsend request')

    message = get_object_or_404(Groupmessage, id=message_id, author=request.user)
    group_name = message.group.group_name
    deleted_id = message.id
    message.delete()

    async_to_sync(get_channel_layer().group_send)(
        group_name,
        {
            'type': 'delete_message_handler',
            'message_id': deleted_id,
        }
    )

    return HttpResponse('')


@login_required
def chat_message_pin(request, message_id):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid pin request')

    message = get_object_or_404(Groupmessage, id=message_id)

    # only allow author to pin/unpin
    if message.author != request.user:
        return HttpResponseBadRequest('Unauthorized')

    if not message.pinned:
        message.pinned = True
        message.pinned_by = request.user
        message.pinned_at = timezone.now()
    else:
        message.pinned = False
        message.pinned_by = None
        message.pinned_at = None

    message.save()

    # broadcast update so other clients can refresh this message
    async_to_sync(get_channel_layer().group_send)(
        message.group.group_name,
        {
            'type': 'message_update_handler',
            'message_id': message.id,
        }
    )

    return render(request, 'a_rtchat/chat_message.html', {'message': message, 'user': request.user})


@login_required
def start_call(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    caller = request.POST.get('caller') or request.user.username
    chatroom_name = request.POST.get('chatroom_name')
    if not chatroom_name:
        return HttpResponseBadRequest('Missing chatroom')

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        chatroom_name,
        {
            'type': 'call_handler',
            'caller': caller,
        }
    )

    # also return the rendered partial so the requester sees the notification immediately
    return render(request, 'a_rtchat/partials/call_notification_p.html', {'caller': caller})


@login_required
def get_call_info(request, call_id):
    """Get video call information"""
    try:
        call = VideoCall.objects.select_related('caller', 'receiver').get(id=call_id)
        
        # Check if user is involved in this call
        if request.user not in [call.caller, call.receiver]:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        return JsonResponse({
            'call_id': call.id,
            'caller': call.caller.username,
            'receiver': call.receiver.username,
            'status': call.status,
            'duration': call.call_duration,
            'answered_at': call.answered_at.isoformat() if call.answered_at else None,
        })
    except VideoCall.DoesNotExist:
        return JsonResponse({'error': 'Call not found'}, status=404)


@login_required
def end_video_call(request, call_id):
    """End video call"""
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    
    try:
        call = VideoCall.objects.get(id=call_id)
        
        # Check if user is involved in this call
        if request.user not in [call.caller, call.receiver]:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # This is handled by the consumer, just return success
        return JsonResponse({'status': 'success'})
    except VideoCall.DoesNotExist:
        return JsonResponse({'error': 'Call not found'}, status=404)

    