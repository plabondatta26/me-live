from django.db import models
from accounts.models import User
    
class LastChatMessage(models.Model):
    chat_id = models.CharField(max_length=200)
    key = models.CharField(max_length=200,blank=True,null=True)
    user_id = models.PositiveIntegerField(default=0,db_index=True)
    sender_id = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=20)
    message = models.CharField(max_length=200,blank=True,null=True)
    full_name = models.CharField(max_length=200)
    profile_image = models.CharField(max_length=250,blank=True,null=True)
    datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat ID: {self.chat_id}, User ID: {self.user_id}"
    
class ChatMessage(models.Model):
    chat_id = models.CharField(max_length=200,db_index=True)
    key = models.CharField(max_length=200,blank=True,null=True)
    sender_id = models.PositiveIntegerField(default=0)
    receiver_id = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=20)
    message = models.TextField(blank=True,null=True)
    datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat ID: {self.chat_id}, Message ID: {self.id}"
    
class ChatBlock(models.Model):
    user_id = models.PositiveBigIntegerField(default=0)
    blocks = models.ManyToManyField(User)

    def __str__(self):
        return f"User ID: {self.user_id}"
