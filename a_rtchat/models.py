from django.db import models
from django.conf import settings
from django.db.models import Count
from django.templatetags.static import static

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=125, unique=True)
    title = models.CharField(max_length=125, blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_groups')
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_groups', blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='group_memberships', blank=True)
    users_name = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='online_in_groups', blank=True)

    def __str__(self):
        return self.display_name()

    def display_name(self):
        return self.title or self.group_name

    def is_member(self, user):
        return user and self.members.filter(id=user.id).exists()

    def is_admin(self, user):
        if not user or user.is_anonymous:
            return False
        return user == self.owner or self.admins.filter(id=user.id).exists()

    def add_member(self, user):
        self.members.add(user)

    def remove_member(self, user):
        self.members.remove(user)
        if self.users_name.filter(id=user.id).exists():
            self.users_name.remove(user)


class Groupmessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    created = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    pinned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='pinned_messages')
    pinned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.file and self.body:
            return f'{self.author.username}: {self.body} + file'
        if self.file:
            return f'{self.author.username}: file {self.file.name}'
        return f'{self.author.username}: {self.body}'

    class Meta:
        ordering = ['-pinned', '-created']

    @property
    def has_file(self):
        return bool(self.file)

    @property
    def reaction_counts(self):
        counts = self.reactions.values('emoji').annotate(count=Count('id')).order_by('-count')
        return {item['emoji']: item['count'] for item in counts}

    def reaction_count(self, emoji):
        return self.reactions.filter(emoji=emoji).count()

    @property
    def heart_reaction_count(self):
        return self.reaction_count('❤️')

    @property
    def receipt_status(self):
        if self.read:
            return 'read'
        if self.delivered:
            return 'delivered'
        return 'sent'

    @property
    def thumbs_reaction_count(self):
        return self.reaction_count('👍')


class Reaction(models.Model):
    message = models.ForeignKey(Groupmessage, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user', 'emoji')

    def __str__(self):
        return f'{self.user.username} reacted {self.emoji} to {self.message.id}'


class VideoCall(models.Model):
    CALL_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('missed', 'Missed'),
        ('completed', 'Completed'),
    ]
    
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='initiated_calls')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_calls')
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='video_calls')
    status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, default='initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    call_duration = models.IntegerField(default=0, help_text='Duration in seconds')

    def __str__(self):
        return f'Call from {self.caller.username} to {self.receiver.username}'

    class Meta:
        ordering = ['-created_at']

    