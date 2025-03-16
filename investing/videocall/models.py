from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Room(models.Model):
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Video Call Room")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.room_id})"

    def is_participant(self, user):
        """Check if user is either instructor or student in this room"""
        return user == self.creator
