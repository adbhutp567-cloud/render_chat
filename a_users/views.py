from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from allauth.account.models import EmailAddress
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from .forms import *
from .models import StatusReaction

User = get_user_model()

def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username)
    elif request.user.is_authenticated:
        profile = request.user
    else:
        return redirect('account_login')

    status_reactions = profile.status_reaction_counts if profile.status_active else {}
    user_reacted_emojis = profile.status_reacted_by_user(request.user) if request.user.is_authenticated else []

    return render(request, 'a_users/profile.html', {
        'profile': profile,
        'status_reactions': status_reactions,
        'user_reacted_emojis': user_reacted_emojis,
    })


@login_required
def profile_status_delete(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    request.user.status = ''
    request.user.status_image = None
    request.user.status_updated_at = None
    request.user.save()
    return redirect('profile')


@login_required
def profile_status_react(request, username):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    emoji = request.POST.get('emoji')
    if not emoji:
        return HttpResponseBadRequest('Missing emoji')

    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return HttpResponseBadRequest('Cannot react to your own status')
    if not target_user.status_active:
        return HttpResponseBadRequest('Status not active')

    reaction, created = StatusReaction.objects.get_or_create(owner=target_user, user=request.user, emoji=emoji)
    if not created:
        reaction.delete()

    return redirect('profile', username=target_user.username)


@login_required
def profile_edit_view(request):
    form = ProfileForm(instance=request.user)  
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        
    if request.path == reverse('profile-onboarding'):
        onboarding = True
    else:
        onboarding = False
      
    return render(request, 'a_users/profile_edit.html', { 'form':form, 'onboarding':onboarding })


@login_required
def profile_settings_view(request):
    return render(request, 'a_users/profile_settings.html')


@login_required
def profile_emailchange(request):
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'partials/email_form.html', {'form':form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)

        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if the email already exists
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            
            form.save() 
            
            # When using email confirmation locally in terminal, remove the = in the confirmation link!
            email_address = EmailAddress.objects.get(user=request.user, email=request.user.email)
            email_address.send_confirmation(request)
            
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Form not valid')
            return redirect('profile-settings')
        
    return redirect('home')


@login_required
def profile_emailverify(request):
    email_address = EmailAddress.objects.get(user=request.user, email=request.user.email)
    email_address.send_confirmation(request)
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    
    return render(request, 'a_users/profile_delete.html')