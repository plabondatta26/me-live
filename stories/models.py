import uuid
import os
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver 
from accounts.models import User

def story_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('stories/images/',filename) 

class Story(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    caption = models.CharField(max_length=250,blank=True,null=True)
    image   = models.ImageField(upload_to=story_image_path,blank=True,null=True)
    likes = models.ManyToManyField(User,related_name='story_likes')
    views = models.ManyToManyField(User,related_name='story_views')

    created_datetime = models.DateTimeField(auto_now_add=True)
    expired_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

    class Meta:
        ordering = ['-expired_datetime']

    def __str__(self):
        return f'{self.user.profile.full_name} > {self.id}' 

class CoverStory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    stories = models.ManyToManyField(Story)
    expired_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

    class Meta:
        verbose_name_plural = 'Cover Stories'

@receiver(post_delete,sender=Story)
def story_submission_delete(sender,instance,**kwargs):
    instance.image.delete(False)