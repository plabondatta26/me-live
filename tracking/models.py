from django.utils import timezone
from django.core.cache import cache
from django.db import models
from profiles.models import Profile
from devices.models import UserDeviceBlocked
from accounts.models import User

class AppLock(models.Model):
	build_number = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		try:
			cache.delete('build_number')
		except:
			pass
		cache.set('build_number',self.build_number,timeout=60*60*24*7)
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "App Lock"

	def __str__(self):
		return f"App Lock ({self.id})"

# Create your models here.
class TotalUsersAndDiamonds(models.Model):
	total_users = models.BigIntegerField(default=0)
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		profile_objs = Profile.objects.all()
		self.total_users = profile_objs.count()

		diamonds = 0
		for profile_obj in profile_objs:
			diamonds += profile_obj.diamonds
		self.total_diamonds = diamonds
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Total Users and Diamonds'

	def __str__(self):
		return f"Total users: {self.total_users} > Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class AccountDeleteAndUsernameChangeDiamonds(models.Model):
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Account Delete and Username Change Diamonds"

	def __str__(self):
		return f"Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class GiftSendVatDiamonds(models.Model):
	gift_vat_diamonds = models.BigIntegerField(default=0)
	live_lock_vat_diamonds = models.BigIntegerField(default=0)

	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Gift Send Vats Diamonds"

	def __str__(self):
		return f"Gift Vat diamonds: {self.gift_vat_diamonds} > Live Lock Vat diamonds: {self.live_lock_vat_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"
	
class ChatSendVatDiamonds(models.Model):
	chat_vat_diamonds = models.BigIntegerField(default=0)

	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Chat Send Vats Diamonds"

	def __str__(self):
		return f"Chat Vat diamonds: {self.chat_vat_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class ReferBonusDiamonds(models.Model):
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Refer Bonus Diamonds"

	def __str__(self):
		return f"Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class FlyingMessageAndBoostDiamonds(models.Model):
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Flying Message and Boost Diamonds"

	def __str__(self):
		return f"Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class WithdrawDiamonds(models.Model):
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Withdraw Diamonds"

	def __str__(self):
		return f"Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class RechargeDiamonds(models.Model):
	total_diamonds = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Recharge Diamonds"

	def __str__(self):
		return f"Total diamonds: {self.total_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class TotalDeviceBlocks(models.Model):
	total_blocks = models.BigIntegerField(default=0)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.total_blocks = UserDeviceBlocked.objects.all().count()
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Total Device Blocks"

	def __str__(self):
		return f"Total blocks: {self.total_blocks} > Updated: {str(self.updated_datetime).split('.')[0]}"


class GamesDiamonds(models.Model):
	invested_diamonds = models.BigIntegerField(default=0)
	recent_diamonds = models.BigIntegerField(default=0)

	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Games Diamonds"

	def __str__(self):
		return f"Invested diamonds: {self.invested_diamonds} > Recent diamonds: {self.recent_diamonds} > Updated: {str(self.updated_datetime).split('.')[0]}"

class BroadcasterHistory(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE)
	audio_broadcast_in_second = models.BigIntegerField(default=0)
	video_broadcast_in_second = models.BigIntegerField(default=0)
	broadcasting_date = models.DateField(auto_now_add=True,)
	updated_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,blank=True,null=True)

	def save(self, *args, **kwargs):
		self.updated_datetime = timezone.now()
		super().save(*args, **kwargs)

	class Meta:
	    verbose_name_plural = "Broadcaster Histories"
	    ordering = ['-broadcasting_date',]

	def __str__(self):
		return f"UserId: {self.user.id}> Audio: {self.audio_broadcast_in_second} seconds > Video: {self.video_broadcast_in_second} seconds > Date: {str(self.broadcasting_date).split('.')[0]}"


class ClearBroadcasterHistory(models.Model):
	make_clear_all_broadcasters_histories = models.CharField(max_length=4,null=True,blank=True,help_text="Type 'Zero' and Save it (It's Case Sensitive)")
	last_clear_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

	def save(self, *args, **kwargs):
		if self.make_clear_all_broadcasters_histories == "Zero":
			BroadcasterHistory.objects.all().delete()
			self.last_clear_datetime = timezone.now()
			self.make_clear_all_broadcasters_histories = ''
		
		super().save(*args, **kwargs)
	
	class Meta:
		verbose_name_plural = 'Removing All Broadcaster Histories'

	def __str__(self):
		return f"Removing Table: {self.id}"