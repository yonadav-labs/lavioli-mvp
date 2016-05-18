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

	def __unicode__(self):
		return self.name
		
		
class TeamUser(AbstractUser):
	"""
	Team user class, it could be team owner, too.
	"""
	team = models.ManyToManyField('Team', related_name="team")
	account = models.ForeignKey(Account, related_name="account")

	def __unicode__(self):
		return self.username


class Team(models.Model):
	"""
	team class
	"""
	name = models.CharField(max_length=50)
	owner = models.ForeignKey(TeamUser, related_name="owner")
	member = models.ManyToManyField(TeamUser, related_name='team_member')
	service = models.ManyToManyField(Service, related_name='team_service')
	is_active = models.BooleanField(default=True)

	def __unicode__(self):
		return self.name
