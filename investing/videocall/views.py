from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Room
import uuid
from django.contrib.auth import get_user_model
import time
import hmac
import hashlib
import base64
import json

# Create your views here.

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            # Create a new room
            room = Room.objects.create(
                name=room_name,
                creator=request.user
            )
            return redirect('videocall:join_room', room_id=room.room_id)
    
    return render(request, 'videocall/create_room.html')

@login_required
def join_room(request, room_id):
    # Try to get the room if it exists
    room = None
    try:
        room = Room.objects.get(room_id=room_id)
    except Room.DoesNotExist:
        # Room doesn't exist in our database, but we'll still allow joining
        # This enables joining rooms by ID even if they weren't created in our system
        pass
    
    user_id = str(request.user.id)
    user_name = request.user.username
    
    context = {
        'room_id': room_id,
        'user_id': user_id,
        'user_name': user_name,
    }
    
    return render(request, 'videocall/room.html', context)

@login_required
def room_list(request):
    # Get rooms created by the current user
    rooms = Room.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'videocall/room_list.html', {'rooms': rooms})
