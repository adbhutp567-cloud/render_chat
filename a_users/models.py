from datetime import timedelta

from django.db import models
from django.db.models import Count
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static
from django.utils import timezone

class CustomUser(AbstractUser):
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=160, null=True, blank=True)
    status_image = models.ImageField(upload_to='status_images/', null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)
    blocked_users = models.ManyToManyField('self', symmetrical=False, related_name='blocked_by', blank=True)

    def __str__(self):
        return self.username
    
    def block(self, user):
        if user != self:
            self.blocked_users.add(user)

    def unblock(self, user):
        if user != self:
            self.blocked_users.remove(user)

    def is_blocked_by(self, user):
        return self in user.blocked_users.all()

    def is_blocking(self, user):
        return self.blocked_users.filter(id=user.id).exists()

    def save(self, *args, **kwargs):
        if self.pk:
            old = CustomUser.objects.filter(pk=self.pk).first()
            if old and (old.status != self.status or old.status_image != self.status_image):
                self.status_updated_at = timezone.now()
        elif (self.status or self.status_image) and not self.status_updated_at:
            self.status_updated_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def status_active(self):
        if not (self.status or self.status_image):
            return False
        if not self.status_updated_at:
            return False
        return self.status_updated_at >= timezone.now() - timedelta(hours=24)

    @property
    def status_image_url(self):
        try:
            return self.status_image.url
        except:
            return None

    @property
    def status_reaction_counts(self):
        counts = self.status_reactions_received.values('emoji').annotate(count=Count('id')).order_by('-count')
        return {item['emoji']: item['count'] for item in counts}

    def status_reacted_by_user(self, user):
        if not user.is_authenticated:
            return []
        return list(self.status_reactions_received.filter(user=user).values_list('emoji', flat=True))

    @property
    def name(self):
        if self.displayname:
            name = self.displayname
        else:
            name = self.username 
        return name
    
    @property
    def avatar(self):
        try:
            avatar = self.image.url
        except:
            avatar = static('images/avatar.svg')
        return avatar


class StatusReaction(models.Model):
    owner = models.ForeignKey('CustomUser', related_name='status_reactions_received', on_delete=models.CASCADE)
    user = models.ForeignKey('CustomUser', related_name='status_reactions_given', on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'user', 'emoji')

    def __str__(self):
        return f'{self.user.username} reacted {self.emoji} to {self.owner.username} status'
