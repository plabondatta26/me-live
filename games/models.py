import json
from django.db import models
from accounts.models import User

# 'mango',
# 'strawberry',
# 'coconut',
# 'apple',
# 'cucumber',
# 'pineapple',

class FortuneWheelPeriodicTracker(models.Model):
	game = models.OneToOneField("FortuneWheel",on_delete=models.CASCADE,related_name="fortune_wheel_tracker")
	# Tracking
	seconds = models.IntegerField(default=0)
	repeats = models.IntegerField(default=0)

	def clear_fields(self):
		self.seconds = 0
		self.repeats = 0
		self.save(force_update=True)

class FortuneWheel(models.Model):
	mango = models.BigIntegerField(default=0)
	mango_times = models.IntegerField(default=6)
	mango_choosers = models.ManyToManyField(User,related_name='mango_choosers',blank=True,)
	mango_played_diamonds = models.TextField(default="{}")
	strawberry = models.BigIntegerField(default=0)
	strawberry_times = models.IntegerField(default=6)
	strawberry_choosers = models.ManyToManyField(User,related_name='strawberry_choosers',blank=True,)
	strawberry_played_diamonds = models.TextField(default="{}")
	coconut = models.BigIntegerField(default=0)
	coconut_times = models.IntegerField(default=6)
	coconut_choosers = models.ManyToManyField(User,related_name='coconut_choosers',blank=True,)
	coconut_played_diamonds = models.TextField(default="{}")
	apple = models.BigIntegerField(default=0)
	apple_times = models.IntegerField(default=6)
	apple_choosers = models.ManyToManyField(User,related_name='apple_choosers',blank=True,)
	apple_played_diamonds = models.TextField(default="{}")
	cucumber = models.BigIntegerField(default=0)
	cucumber_times = models.IntegerField(default=6)
	cucumber_choosers = models.ManyToManyField(User,related_name='panda_choosers',blank=True,)
	cucumber_played_diamonds = models.TextField(default="{}")
	pineapple = models.BigIntegerField(default=0)
	pineapple_times = models.IntegerField(default=6)
	pineapple_choosers = models.ManyToManyField(User,related_name='pineapple_choosers',blank=True,)
	pineapple_played_diamonds = models.TextField(default="{}")
	# melon = models.BigIntegerField(default=0)
	# melon_times = models.IntegerField(default=6)
	# melon_choosers = models.ManyToManyField(User,related_name='lion_choosers',blank=True,)
	# melon_played_diamonds = models.TextField(default="{}")
	# banana = models.BigIntegerField(default=0)
	# banana_times = models.IntegerField(default=6)
	# banana_choosers = models.ManyToManyField(User,related_name='banana_choosers',blank=True,)
	# banana_played_diamonds = models.TextField(default="{}")

	viewers = models.ManyToManyField(User,related_name='viewers',blank=True,)
	players = models.ManyToManyField(User,related_name='players',blank=True,)
	winner_index = models.IntegerField(default=-1)
	played_diamonds = models.TextField(default=json.dumps([]))
	top_played_diamonds = models.TextField(default=json.dumps([]))
	winning_diamonds = models.TextField(default="{}")
	winner_history = models.CharField(max_length=200,blank=True,null=True)
	updated_datetime = models.DateTimeField(auto_now=True)

	def clear_fields(self):
		self.mango = 0
		self.mango_choosers.clear()
		self.mango_played_diamonds = "{}"
		self.strawberry = 0
		self.strawberry_choosers.clear()
		self.strawberry_played_diamonds = "{}"
		self.coconut = 0
		self.coconut_choosers.clear()
		self.coconut_played_diamonds = "{}"
		self.apple = 0
		self.apple_choosers.clear()
		self.apple_played_diamonds = "{}"
		self.cucumber = 0
		self.cucumber_choosers.clear()
		self.cucumber_played_diamonds = "{}"
		self.pineapple = 0
		self.pineapple_choosers.clear()
		self.pineapple_played_diamonds = "{}"
		# self.melon = 0
		# self.melon_choosers.clear()
		# self.melon_played_diamonds = "{}"
		# self.banana = 0
		# self.banana_choosers.clear()
		# self.banana_played_diamonds = "{}"
		self.players.clear()
		self.winner_index = -1
		self.played_diamonds = json.dumps([])
		self.top_played_diamonds = json.dumps([])
		self.winning_diamonds = "{}"
		self.save(force_update=True)

		self.fortune_wheel_tracker.clear_fields()

	# def save(self, *args, **kwargs):
	# 	self.updated_datetime = timezone.now()
	# 	super().save(*args, **kwargs)

	class Meta:
		verbose_name_plural = 'Fortune Wheel'

	def __str__(self):
		return f"Fortune Wheel ID: {self.id}"
