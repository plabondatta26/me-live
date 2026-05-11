import uuid
import os
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver 
from accounts.models import User

def support_post_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('support/post_images/',filename) 

class SupportPost(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    text = models.TextField(blank=True,null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     super(SupportPost, self).save(*args, **kwargs)


    class Meta:
        ordering = ['-id',]

    def __str__(self):
        return f'Support Post > {self.id}' 

class SupportPostImage(models.Model):
    post = models.ForeignKey(SupportPost,on_delete=models.CASCADE,related_name='support_post_images')
    image   = models.ImageField(upload_to=support_post_image_path, )

    created_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Images'
        ordering = ['-id']

    def __str__(self):
        return f'Support Post Image > {self.id}' 


class SupportPostReply(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    post = models.ForeignKey(SupportPost,on_delete=models.CASCADE,related_name='support_post_replies')
    text = models.TextField()
    
    created_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Replies'
        ordering = ['-id']

    def __str__(self):
        return f'Reply > {self.id}' 

@receiver(post_delete,sender=SupportPostImage)
def support_post_image_submission_delete(sender,instance,**kwargs):
    instance.image.delete(False)
