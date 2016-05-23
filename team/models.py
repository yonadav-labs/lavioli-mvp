from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractUser


class Service(models.Model):
	"""
	Service models.Model
	needs to be modified
	"""
	name = models.CharField(max_length=50)
	token = models.CharField(max_length=200)
	is_active = models.BooleanField(default=True)
	# more fields

	def __unicode__(self):
		return self.name


class Account(models.Model):
	"""
	Account level class
	"""
	name = models.CharField(max_length=50)
	team_limit = models.IntegerField(default=0)
	budget = models.IntegerField(default=0)
	description = models.TextField(null=True, blank=True)
	stripe_id = models.CharField(max_length=50)

	def __unicode__(self):
		return self.name
		
		
class TeamUser(AbstractUser):
	"""
	Team user class, it could be team owner, too.
	"""
	account = models.ForeignKey(Account, related_name="account", null=True, blank=True)
	is_temp = models.BooleanField(default=False)
	exp_date = models.DateField(null=True, blank=True)
	last4_card_num = models.CharField(max_length=4, null=True, blank=True)
	phone = models.CharField(max_length=20, null=True, blank=True)
	customer_id = models.CharField(max_length=50, null=True, blank=True)
	subscription_id = models.CharField(max_length=50, null=True, blank=True)

	def __unicode__(self):
		return self.username


class Team(models.Model):
	"""
	team class
	"""
	name = models.CharField(max_length=50)
	owner = models.ForeignKey(TeamUser, related_name="owner")
	member = models.ManyToManyField(TeamUser, related_name='team_member', blank=True)
	service = models.ManyToManyField(Service, related_name='team_service', blank=True)
	is_active = models.BooleanField(default=True)

	def __unicode__(self):
		return self.name
