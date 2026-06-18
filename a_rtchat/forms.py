from django.forms import ModelForm
from django import forms
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .models import ChatGroup, Groupmessage

class ChatmessageCreateFrom(ModelForm):
    class Meta:
        model = Groupmessage
        fields = ['body', 'file']
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Add message...',
                'class': 'py-2 px-3 w-full rounded-2xl bg-white text-black text-sm md:text-sm lg:text-sm',
                'maxlength': '300',
                'autofocus': True,
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'mt-2 w-full text-sm text-white file:bg-slate-700 file:text-white file:py-2 file:px-3 file:rounded-lg',
                'accept': 'image/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }),
        }


class CreateGroupForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['title', 'group_name']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Group title',
                'class': 'w-full rounded-2xl border border-slate-700/80 bg-slate-950/90 px-3 py-2 text-sm text-slate-100',
            }),
            'group_name': forms.TextInput(attrs={
                'placeholder': 'URL slug (optional)',
                'class': 'w-full rounded-2xl border border-slate-700/80 bg-slate-950/90 px-3 py-2 text-sm text-slate-100',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get('title', '').strip()
        raw_group_name = cleaned.get('group_name', '').strip()

        if not title:
            raise ValidationError('A group title is required.')

        if raw_group_name:
            group_name = slugify(raw_group_name)
        else:
            group_name = slugify(title)

        if not group_name:
            raise ValidationError('Please enter a valid group name.')

        if group_name == 'uptti' or group_name.startswith('private-'):
            raise ValidationError('That group name is reserved.')

        if ChatGroup.objects.filter(group_name=group_name).exists():
            raise ValidationError('A group with that URL slug already exists.')

        cleaned['group_name'] = group_name
        cleaned['title'] = title
        return cleaned
