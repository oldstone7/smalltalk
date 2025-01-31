
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegisterForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Message
from django.db.models import Q, Max
from django.db.models import OuterRef, Subquery


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            print('User created')
            return redirect('login')  # Redirect to user list after registration
    else:
        form = UserRegisterForm()
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_list')
        else:
            errors = {"username": "Invalid username or password"}  # Error message
            return render(request, "chat/login.html", {"errors": errors})  # Pass errors to template
    else:
        form = AuthenticationForm()
        
    return render(request, 'chat/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)

    last_message_subquery = Message.objects.filter(
        Q(sender=OuterRef('pk'), receiver=request.user) |
        Q(sender=request.user, receiver=OuterRef('pk'))
    ).order_by('-timestamp').values('content')[:1]

    

    users = users.annotate(
        last_message=Subquery(last_message_subquery.values('content')[:1]),
        last_message_timestamp=Subquery(last_message_subquery.values('timestamp')[:1])
    )
    return render(request, 'chat/user_list.html', {'users': users})


@login_required
def chat(request, user_id):
    users = User.objects.exclude(id=request.user.id)
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')


    # Subquery to get the last message for each user relative to the logged-in user
    last_message_subquery = Message.objects.filter(
        Q(sender=OuterRef('pk'), receiver=request.user) |
        Q(sender=request.user, receiver=OuterRef('pk'))
    ).order_by('-timestamp').values('content')[:1]

    users = users.annotate(
        last_message=Subquery(last_message_subquery.values('content')[:1]),
        last_message_timestamp=Subquery(last_message_subquery.values('timestamp')[:1])
    )
    return render(request, 'chat/chat.html', { 
        'other_user': other_user, 
        'messages': messages, 
        'users': users,    
    })

