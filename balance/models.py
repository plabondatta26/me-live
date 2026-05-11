import uuid
import os 
from django.utils import timezone
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver 
from accounts.models import User
from products.models import WithdrawPackage
from tracking.models import WithdrawDiamonds
from balance.utils import (
    custom_unique_slug_generator_for_title,
) 

def payment_method_logo_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('balance/payment_method_logos/',filename) 

# def deposit_screenshot_image_path(instance, filename):
#     ext = filename.split('.')[-1]
#     filename = f'{uuid.uuid4()}.{ext}'

#     return os.path.join('balance/deposit_screenshot_images/',filename) 

# class Balance(models.Model): 
#     user = models.OneToOneField(User,on_delete=models.CASCADE) 
#     amount = models.DecimalField(max_digits=8,decimal_places=2,default=0.0)    
#     earn_coins = models.IntegerField(default=0)    
#     updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

#     class Meta:
#         verbose_name_plural = 'User Balance'
#         ordering = ['-id']

#     def __str__(self):
#         return f"{self.user.profile.full_name} > Balance: {self.amount} > Updated: {str(self.updated_datetime).split('.')[0]}"

# class EarnCoinExchanger(models.Model): 
#     per_coin_rate = models.DecimalField(max_digits=6,decimal_places=2,default=0.25)    

#     def save(self, *args, **kwargs):
#         if EarnCoinExchanger.objects.first() is not None:
#             return
#         super().save(*args, **kwargs)

#     class Meta:
#         verbose_name_plural = "Earn Coin Exchanger Rule (in BDT) (Don't add multiple rule)"

#     def __str__(self):
#         return f"1 coin = {self.per_coin_rate} BDT"

class PaymentMethodAccountType(models.Model):
    payment_method = models.ForeignKey('PaymentMethod',on_delete=models.CASCADE)
    title = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.payment_method.title} > {self.title}" 

class PaymentMethod(models.Model): 
    title = models.CharField(max_length=25)
    # Custom Slug
    slug = models.CharField(max_length=30,unique=True,blank=True,null=True)
    logo   = models.ImageField(upload_to=payment_method_logo_path)

    charge = models.DecimalField(max_digits=8,decimal_places=2,default=0.0)    
    created_datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Payment Methods'
        ordering = ['id']

    def __str__(self):
        return self.title 

# class DepositRequest(models.Model): 
#     user = models.ForeignKey(User,on_delete=models.CASCADE) 
#     payment_method = models.ForeignKey(PaymentMethod,on_delete=models.SET_NULL,blank=True,null=True)

#     screenshot   = models.ImageField(upload_to=deposit_screenshot_image_path)
#     amount = models.DecimalField(max_digits=8,decimal_places=2)    
#     sender_number = models.CharField(max_length=50)
#     transaction_id = models.CharField(max_length=50,null=True,blank=True)
#     feedback = models.CharField(max_length=350,null=True,blank=True)

#     is_pending = models.BooleanField(default=True)
#     is_accepted = models.BooleanField(default=False)
#     is_declined = models.BooleanField(default=False)

#     requested_datetime = models.DateTimeField(auto_now_add=True)
#     updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

#     def save(self, *args, **kwargs):
#         # Restrict user not to update again
#         if self.updated_datetime is not None:
#             return
#         if self.is_accepted:
#             balance_obj = Balance.objects.filter(user=self.user).first()
#             if balance_obj is None:
#                 balance_obj = Balance() 
#                 balance_obj.user = self.user
#                 balance_obj.amount = self.amount
#             else:
#                 balance_obj.amount += self.amount
#             balance_obj.updated_datetime = timezone.now()
#             balance_obj.save()
#             self.updated_datetime = timezone.now()
            
#         elif self.is_declined:
#             self.updated_datetime = timezone.now()
#         super().save(*args, **kwargs)

#     class Meta:
#         verbose_name_plural = 'Deposit Requests'
#         ordering = ['-id']

#     def __str__(self):
#         status = ''        
#         if self.is_accepted == True:
#             status = 'Accepted'
#         elif self.is_declined == True:
#             status = 'Declined'
#         elif self.is_pending == True:
#             status = 'Pending'
#         return f"{self.user.profile.full_name} > {str(self.requested_datetime).split('.')[0]} > {status}"

class WithdrawRequest(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE) 
    payment_method = models.ForeignKey(PaymentMethod,on_delete=models.SET_NULL,blank=True,null=True)
    withdraw_package = models.ForeignKey(WithdrawPackage,on_delete=models.SET_NULL,blank=True,null=True)

    payment_method_name = models.CharField(max_length=20)
    account_type = models.CharField(max_length=20,null=True,blank=True)
    diamonds = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=8,decimal_places=2)    
    received_amount = models.DecimalField(max_digits=8,decimal_places=2)    
    receiver_number = models.CharField(max_length=50)
    feedback = models.CharField(max_length=350,null=True,blank=True)
    
    is_pending = models.BooleanField(default=True)
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)

    requested_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

    def save(self, *args, **kwargs):
        # Restrict user not to update again
        if self.updated_datetime is not None:
            return
        if self.is_accepted:
            withdraw_diamonds_obj = WithdrawDiamonds.objects.first()
            if withdraw_diamonds_obj is None:
                withdraw_diamonds_obj = WithdrawDiamonds()
                withdraw_diamonds_obj.total_diamonds = self.diamonds
            else:
                withdraw_diamonds_obj.total_diamonds += self.diamonds
            withdraw_diamonds_obj.save()
            self.updated_datetime = timezone.now()

        elif self.is_declined:
            self.user.profile.diamonds += self.diamonds
            self.user.profile.save()
            self.updated_datetime = timezone.now()
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Withdraw Requests'
        ordering = ['-id']

    def __str__(self):
        status = ''
        if self.is_accepted == True:
            status = 'Accepted'
        elif self.is_declined == True:
            status = 'Declined'
        elif self.is_pending == True:
            status = 'Pending'
        return f"{self.user.profile.full_name} > {str(self.requested_datetime).split('.')[0]} > {status}"

# class Plan(models.Model):
#     name = models.CharField(max_length=100)
#     receive_call_type = models.CharField(max_length=5,default='video',verbose_name="Use 'video' or 'audio'")
#     price = models.DecimalField(max_digits=8,decimal_places=2)    
#     days = models.IntegerField(verbose_name='Validity Days',default=0)

#     def save(self, *args, **kwargs):
#         # Restrict user to user only 'audio' and 'video' slug
#         if self.receive_call_type != 'audio' and self.receive_call_type != 'video':
#             return
        
#         super().save(*args, **kwargs)

#     class Meta:
#         ordering = ['price']

#     def __str__(self):
#         return f"{self.name} > Price: {self.price} > Validity: {self.days} days"

# class PlanPurchased(models.Model):
#     user = models.ForeignKey(User,on_delete=models.CASCADE)
#     plan = models.ForeignKey(Plan,on_delete=models.CASCADE)
#     expired_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

#     class Meta:
#         verbose_name_plural = 'Plan Purchased'
#         ordering = ['expired_datetime']

#     def __str__(self):
#         return f"{self.user.profile.full_name} > Plan: {self.plan.name} > Validity: {str(self.expired_datetime).split('.')[0]}"

# class EarningHistory(models.Model): 
#     user = models.ForeignKey(User,on_delete=models.CASCADE) 
#     gift_sender = models.ForeignKey(User,on_delete=models.CASCADE,related_name='gift_sender') 
#     diamonds = models.IntegerField(default=0)    
#     datetime = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name_plural = 'Earning Histories'
#         ordering = ['-datetime']

#     def __str__(self):
#         return f"{self.user.profile.full_name} > Earn Diamonds: {self.diamonds} > Datetime: {str(self.datetime).split('.')[0]}"

class Contribution(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE) 
    contributor = models.ForeignKey(User,on_delete=models.CASCADE,related_name='contributor') 
    diamonds = models.BigIntegerField(default=0)    
    datetime = models.DateTimeField(auto_now_add=False,auto_now=False)

    class Meta:
        verbose_name_plural = 'Contribution Ranking'
        ordering = ['-diamonds']

    def __str__(self):
        return f"{self.user.profile.full_name} > Contributed Diamonds: {self.diamonds} > Datetime: {str(self.datetime).split('.')[0]}"

class ClearContributionRanking(models.Model):
    make_contribution_ranking_zero = models.CharField(max_length=4,null=True,blank=True,help_text="Type 'Zero' and Save it (It's Case Sensitive)")
    last_contribution_ranking_clear_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)
    upcoming_contribution_ranking_clear_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

    def save(self, *args, **kwargs):
        if self.make_contribution_ranking_zero == "Zero":
            Contribution.objects.all().delete()
            self.last_contribution_ranking_clear_datetime = timezone.now()
        self.make_contribution_ranking_zero = ''
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = 'Clear Contribution Rankings'

    def __str__(self):
        return f"Last clear datetime: {str(self.last_contribution_ranking_clear_datetime)}"

# pre_save.connect(custom_unique_slug_generator_for_title, sender=PaymentMethod)

@receiver(post_delete,sender=PaymentMethod)
def payment_method_submission_delete(sender,instance,**kwargs):
    instance.logo.delete(False)

@receiver(post_delete,sender=WithdrawRequest)
def withdraw_request_submission_delete(sender,instance,**kwargs):
    if instance.updated_datetime is None:
        instance.user.profile.diamonds += instance.diamonds
        instance.user.profile.save()

# @receiver(post_delete,sender=DepositRequest)
# def deposit_request_submission_delete(sender,instance,**kwargs):
#     instance.screenshot.delete(False)
