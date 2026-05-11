import json
from django.db.models.signals import pre_delete
from django.dispatch import receiver 
from django.utils import timezone
from django.db import models
from accounts.models import User
from me_live.utils.utils import DateTimeEncoder, updateProfileInGlobalWebsocket

class ModeratorRequest(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	is_approved = models.BooleanField(default=False)
	is_declined = models.BooleanField(default=False)
	datetime = models.DateTimeField(auto_now_add=True,)

	def save(self, *args, **kwargs):
		if self.is_declined:
			self.delete()
			return
		if self.is_approved:
			moderator_profile_obj = self.user.profile
			if moderator_profile_obj.is_agent or moderator_profile_obj.is_host or moderator_profile_obj.is_reseller or moderator_profile_obj.is_moderator:
				self.delete()
				return
			moderator_obj = Moderator()
			moderator_obj.user = self.user
			moderator_obj.save()
			# Updating moderator profile
			moderator_profile_obj.is_moderator = True
			moderator_profile_obj.be_moderator_datetime = timezone.now()
			moderator_profile_obj.save()
			self.delete()

			updateProfileInGlobalWebsocket(moderator_profile_obj)

			return
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Moderator Requests'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Datetime: {self.datetime}"

class Moderator(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	mobile_number = models.CharField(max_length=16,null=True,blank=True)
	datetime = models.DateTimeField(auto_now_add=True,)
	
	class Meta:
		verbose_name_plural = 'Moderators'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Moderator ID: {self.id}"


class AgentRequest(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	is_approved = models.BooleanField(default=False)
	is_declined = models.BooleanField(default=False)
	datetime = models.DateTimeField(auto_now_add=True,)

	def save(self, *args, **kwargs):
		if self.is_declined:
			self.delete()
			return
		if self.is_approved:
			agent_profile_obj = self.user.profile
			if agent_profile_obj.is_agent or agent_profile_obj.is_host or agent_profile_obj.is_reseller or agent_profile_obj.is_moderator:
				self.delete()
				return
			agent_obj = Agent()
			agent_obj.user = self.user
			agent_obj.save()
			# Updating agent profile
			agent_profile_obj.is_agent = True
			agent_profile_obj.be_agent_datetime = timezone.now()
			agent_profile_obj.save()
			self.delete()

			updateProfileInGlobalWebsocket(agent_profile_obj)

			return
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Agent Requests'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Datetime: {self.datetime}"

class Agent(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	mobile_number = models.CharField(max_length=16,null=True,blank=True)
	make_hosts_diamonds_zero = models.CharField(max_length=4,null=True,blank=True,help_text="Type 'Zero' and Save it (It's Case Sensitive)")
	last_hosts_diamonds_clear_datetime = models.DateTimeField(auto_now_add=False,auto_now=False,null=True,blank=True)

	datetime = models.DateTimeField(auto_now_add=True,)

	hosts = models.ManyToManyField(User,related_name="hosts",blank=True,)
	host_joining_dates = models.TextField(default="{}")

	def save(self, *args, **kwargs):
		if self.make_hosts_diamonds_zero == "Zero":
			host_objs = self.hosts.all()
			if host_objs.count() > 0:
				for user_obj in host_objs:
					profile_obj = user_obj.profile
					profile_obj.diamonds = 0
					profile_obj.save()
				self.last_hosts_diamonds_clear_datetime = timezone.now()
		self.make_hosts_diamonds_zero = ''
		
		super().save(*args, **kwargs)
	
	class Meta:
		verbose_name_plural = 'Agents'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Agent ID: {self.id}"

class HostRequest(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
	is_allow_video_live = models.BooleanField(default=False)
	is_approved = models.BooleanField(default=False)
	is_declined = models.BooleanField(default=False)
	datetime = models.DateTimeField(auto_now_add=True,)

	def save(self, *args, **kwargs):
		if self.is_declined:
			self.delete()
			return
		if self.is_approved:
			if self.user in self.agent.hosts.all():
				self.delete()
			else:
				host_profile_obj = self.user.profile
				if host_profile_obj.is_agent or host_profile_obj.is_host or host_profile_obj.is_reseller or host_profile_obj.is_moderator:
					self.delete()
					return
				json_data = json.loads(self.agent.host_joining_dates)
				json_data[f"{self.user.id}"] = {
                	"datetime": timezone.now(),
                }
                # Added to the agent Table
				self.agent.host_joining_dates = DateTimeEncoder().encode(json_data)
				self.agent.save()
				self.agent.hosts.add(self.user)

				# Updating host profile
				if self.is_allow_video_live:
					host_profile_obj.is_allow_video_live = True
				else:
					host_profile_obj.is_allow_video_live = False 
				host_profile_obj.is_host = True
				host_profile_obj.be_host_datetime = timezone.now()
				host_profile_obj.save()

				updateProfileInGlobalWebsocket(host_profile_obj)

				self.delete()
			return
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Host Requests'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Datetime: {self.datetime}"

class ResellerRequest(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	is_approved = models.BooleanField(default=False)
	is_declined = models.BooleanField(default=False)
	assign_diamonds = models.BigIntegerField(default=0,help_text='Assign diamonds')
	datetime = models.DateTimeField(auto_now_add=True,)

	def save(self, *args, **kwargs):
		if self.is_declined:
			self.delete()
			return
		if self.is_approved:
			reseller_profile_obj = self.user.profile
			if reseller_profile_obj.is_agent or reseller_profile_obj.is_host or reseller_profile_obj.is_reseller or reseller_profile_obj.is_moderator:
				self.delete()
				return
			reseller_obj = Reseller()
			reseller_obj.user = self.user
			if self.assign_diamonds > 0:
				profile_obj = self.user.profile
				profile_obj.diamonds += self.assign_diamonds
				profile_obj.save()
				reseller_obj.last_assigned_diamonds = self.assign_diamonds
			reseller_obj.diamond_updated_datetime = timezone.now()
			reseller_obj.save()
			# Updating reseller profile
			reseller_profile_obj.is_reseller = True
			reseller_profile_obj.be_reseller_datetime = timezone.now()
			reseller_profile_obj.save()
			self.delete()

			updateProfileInGlobalWebsocket(reseller_profile_obj)

			return
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Reseller Requests'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Datetime: {self.datetime}"

class Reseller(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	mobile_number = models.CharField(max_length=16,null=True,blank=True)
	assign_diamonds = models.BigIntegerField(default=0,help_text='Assign diamonds')
	last_assigned_diamonds = models.IntegerField(default=0)

	created_datetime = models.DateTimeField(auto_now_add=True,)
	diamond_updated_datetime = models.DateTimeField(null=True)
	
	def save(self, *args, **kwargs):
		if self.assign_diamonds > 0:
			profile_obj = self.user.profile
			profile_obj.diamonds += self.assign_diamonds
			profile_obj.save()
			updateProfileInGlobalWebsocket(profile_obj)
			self.last_assigned_diamonds = self.assign_diamonds
			self.assign_diamonds = 0
			self.diamond_updated_datetime = timezone.now()
		
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Resellers'
		ordering = ['-created_datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Reseller ID: {self.id}"

class ResellerHistory(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	reseller = models.ForeignKey(Reseller, on_delete=models.CASCADE)
	recharged_diamonds = models.BigIntegerField(default=0,help_text='Rechared diamonds')
	datetime = models.DateTimeField(auto_now_add=True,)
	
	def save(self, *args, **kwargs):
		profile_obj = self.user.profile
		updateProfileInGlobalWebsocket(profile_obj)
		updateProfileInGlobalWebsocket(self.reseller.user.profile)
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Reseller Histories'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Reseller ID: {self.id}"
	
class AgentRechargedHistory(models.Model):
	user = models.ForeignKey(User,on_delete=models.CASCADE,)
	agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
	recharged_diamonds = models.BigIntegerField(default=0,help_text='Rechared diamonds')
	datetime = models.DateTimeField(auto_now_add=True,)
	
	def save(self, *args, **kwargs):
		profile_obj = self.user.profile
		updateProfileInGlobalWebsocket(profile_obj)
		updateProfileInGlobalWebsocket(self.agent.user.profile)
		super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Agent Recharged Histories'
		ordering = ['-datetime']

	def __str__(self):
		return f"User ID: {self.user_id} > Agent ID: {self.agent.id}"

@receiver(pre_delete,sender=Moderator)
def moderator_submission_delete(sender,instance,**kwargs):
	# Delete moderator
	profile_obj = instance.user.profile
	profile_obj.is_moderator = False
	profile_obj.save()
	updateProfileInGlobalWebsocket(profile_obj)

@receiver(pre_delete,sender=Agent)
def agent_submission_delete(sender,instance,**kwargs):
	# Delete Agent
	profile_obj = instance.user.profile
	profile_obj.is_agent = False
	profile_obj.save()
	updateProfileInGlobalWebsocket(profile_obj)

	# Update host profiles
	for host_user_obj in instance.hosts.all():
		host_profile_obj = host_user_obj.profile
		host_profile_obj.is_host = False
		host_profile_obj.save()
		updateProfileInGlobalWebsocket(profile_obj)

@receiver(pre_delete,sender=Reseller)
def reseller_submission_delete(sender,instance,**kwargs):
	# Delete reseller
	profile_obj = instance.user.profile
	profile_obj.is_reseller = False
	profile_obj.save()
	updateProfileInGlobalWebsocket(profile_obj)
