from django.forms import ModelForm
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ['displayname', 'image', 'status', 'status_image']
        widgets = {
            'displayname': forms.TextInput(attrs={
                'placeholder': 'Display name',
                'class': 'form-input',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
            'status': forms.TextInput(attrs={
                'placeholder': 'What are you up to? (Max 160 characters)',
                'class': 'form-input',
            }),
            'status_image': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
        }

class EmailForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email address',
                'class': 'form-input',
            }),
        }
