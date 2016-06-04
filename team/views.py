import hashlib, datetime, random
import stripe
import requests
import json
from datetime import timedelta

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import *

from .models import *
from .forms import *

def dashboard(request):
	return render(request, 'dashboard.html')

@login_required
def team_info(request, id):
	team = Team.objects.get(id=id)
	members = team.member.all()
	services = team.service.all()
	return render(request, 'team_info.html', {
		'team': team,
		'members': members,
		'services': services,
		})

@login_required
def myteam_info(request, id):
	team = Team.objects.filter(id=id, member__email=request.user.email)
	if team:
		team = team[0]
		members = team.member.all()
		services = team.service.all()
		return render(request, 'myteam_info.html', {
			'team': team,
			'members': members,
			'services': services,
			})
	else:
		return HttpResponse('You are not a member of this team!')

@login_required
def add_service(request, id):
	team = Team.objects.get(id=id)
	services = team.service.all()
	# deal with service name
	services = [service.name for service in services]
	other_services = [item[0] for item in SERVICES]
	other_services = list(set(other_services)-set(services))

	return render(request, 'add_service.html', {
		'team': team,
		'services': other_services,
		})

@login_required
def update_account(request):
	teamuser = TeamUser.objects.get(email=request.user.email)
	account = teamuser.account

	other_accounts = Account.objects.all()
	if account:
		other_accounts = other_accounts.exclude(id__in=[account.id])
		

	return render(request, 'update_account.html', {
		'accounts': other_accounts,
		'email': teamuser.email,
		'customer_id': teamuser.customer_id,
		'key': settings.STRIPE_KEYS['publishable_key'],
		})

@login_required
def charge_account(request):
	teamuser = TeamUser.objects.get(email=request.user.email)
	account = Account.objects.get(id=request.POST.get('a_id'))

	card = request.POST.get('stripeToken')
	stripe.api_key = settings.STRIPE_KEYS['stripe_secret_key']

	if not card:	# update subscription
		subscription = stripe.Subscription.retrieve(teamuser.subscription_id)
		subscription.plan = account.stripe_id
		subscription.save()
	else:			# for the first time
		customer = stripe.Customer.create(
			email=teamuser.email,
			plan=account.stripe_id,
			card=card
		)

		teamuser.customer_id = customer.id
		teamuser.subscription_id = customer.subscriptions.data[0].id
		teamuser.last4_card_num = customer.sources.data[0].last4
		teamuser.exp_date = datetime.date.today() + timedelta(days=30)

	teamuser.account = account
	teamuser.save()

	return HttpResponseRedirect('/plan')


GITHUB_ERRORS = {
	'Bad credentials': 'The token you provided is not correct. Please check again!',
	'Not Found': 'There is no such organization. Please check again!',
}

BITBUCKET_ERRORS = {
	401: 'Password is incorrect. Please check again',
}

@login_required
def add_service_real(request, s_name, t_id):
	template = 'service/%s.html' % (s_name.replace(' ', ''))
	if request.method == 'GET':
		if s_name == 'Github':
			form = GithubForm(initial={'name': s_name})
		elif s_name == 'Bitbucket':
			form = BitbucketForm(initial={'name': s_name})
		elif s_name == 'Slack':
			form = SlackForm(initial={'name': s_name})
	else:
		if s_name == 'Github':
			form = GithubForm(request.POST)
			if form.is_valid():
				url = 'https://api.github.com/orgs/%s/teams' % form.cleaned_data['org_name']
				header = {"Authorization": "token "+form.cleaned_data['token']}

				res = requests.get(url=url, headers=header)
				res_json = res.json()
				if type(res_json) is dict:
					form.errors['Error: '] = GITHUB_ERRORS[res_json['message']]
				else:
					team_id = ''
					for team in res_json:
						if team['name'] == form.cleaned_data['team_name']:
							team_id = team['id']
							break
					if team_id == '':
						form.errors['Error: '] = 'There is no such team. Please check again!'
					else:						
						service = Service()
						service.name = s_name
						service.token = form.cleaned_data['token']
						service.org_name = form.cleaned_data['org_name']
						service.team_name = form.cleaned_data['team_name']
						service.team_id = team_id
						service.save()

						team = Team.objects.get(id=t_id)
						team.service.add(service)
						team.save()

						send_invitation_github_team(team, service)
						return HttpResponseRedirect('/team/'+t_id)
		elif s_name == 'Bitbucket':
			form = BitbucketForm(request.POST)
			if form.is_valid():
				team = Team.objects.get(id=t_id)
				url = 'https://api.bitbucket.org/1.0/groups/%s/' % team.owner.email
				res = requests.get(url=url, auth=(team.owner.email, form.cleaned_data['password']))
				flag = False
				if res.status_code != 200:
					form.errors['Error: '] = BITBUCKET_ERRORS[res.status_code]
				else:
					res_json = res.json()
					group_slug = get_slug(form.cleaned_data['group_name'])
					for group in res_json:
						if group['slug'] == group_slug:
							flag = True
							break
					if not flag:
						form.errors['Error: '] = 'There is no such organization. Please check again!'
					else:						
						service = Service()
						service.name = s_name
						service.token = form.cleaned_data['password']
						service.org_name = group_slug
						service.save()

						team = Team.objects.get(id=t_id)
						team.service.add(service)
						team.save()

						add_member_bitbucket_group(team, service)
						return HttpResponseRedirect('/team/'+t_id)
		elif s_name == 'Slack':
			form = SlackForm(request.POST)
			if form.is_valid():
				team = Team.objects.get(id=t_id)
				url = 'https://slack.com/api/auth.test?token=%s&email=any@email.com&set_active=true' % form.cleaned_data['team_token']
				res = requests.post(url=url)
				res_json = res.json()
				if res_json['ok'] != True:
					form.errors['Error: '] = 'Team Token is incorrect. Please check again!'
				else:
					service = Service()
					service.name = s_name
					service.token = form.cleaned_data['team_token']
					service.save()

					team = Team.objects.get(id=t_id)
					team.service.add(service)
					team.save()

					add_member_slack_group(team, service)
					return HttpResponseRedirect('/team/'+t_id)


	return render(request, template, {
		'form': form,
		't_id': t_id,
	})

def send_invitation_github_team(team, service):
	'''
	send invitations to team members to github with their emails
	'''
	for member in team.member.all():
		send_invitation_github_individual(member.email, service)

def add_member_bitbucket_group(team, service):
	'''
	add team members to bitbucket with their emails
	'''
	for member in team.member.all():
		add_member_bitbucket_individual(team.owner.email, member.email, service)

def add_member_slack_group(team, service):
	'''
	add team members to slack with their emails
	'''
	for member in team.member.all():
		add_member_slack_individual(member.email, service)

def add_member_slack_individual(email, service):
	url = 'https://anyteam.slack.com/api/users.admin.invite?token=%s&email=%s&set_active=true' % (service.token, email)
	requests.post(url=url)

def add_member_bitbucket_individual(accountemail, email, service):
	url = 'https://api.bitbucket.org/1.0/groups/%s/%s/members/%s' % (accountemail, service.org_name, email)
	data = '{}'
	header = {'Content-Type': 'application/json'}

	r = requests.put(url=url, auth=(accountemail, service.token), data=data, headers=header)

def delete_membership_bitbucket_individual(accountemail, email, service):
	url = 'https://api.bitbucket.org/1.0/groups/%s/%s/members/%s' % (accountemail, service.org_name, email)
	r = requests.delete(url=url, auth=(accountemail, service.token))

def send_invitation_github_individual(email, service):
	'''
	send invitation to a user to github with his email.
	'''
	member_login = get_member_name_with_email_github(email)
	if member_login != '':
		url = 'https://api.github.com/teams/%s/memberships/%s' % (service.team_id, member_login)
		header = {"Authorization": "token "+service.token}
		res = requests.put(url=url, headers=header)
		print res
	else:
		print "Email {} did not correspond to a user".format(email)

def delete_membership_github_individual(email, service):
	'''
	delete membership of the user to github service with his email.
	'''
	member_login = get_member_name_with_email_github(email)
	if member_login != '':
		url = 'https://api.github.com/teams/%s/memberships/%s' % (service.team_id, member_login)
		header = {"Authorization": "token "+service.token}
		res = requests.delete(url=url, headers=header)		

def get_member_name_with_email_github(email):	
	'''
	get login from an existing user on github with his email.
	return login if success, empty string if not
	'''
	url = 'https://api.github.com/search/users?q=%s+in%%3Aemail' % email
	res = requests.get(url=url)
	res_json = res.json()
	if int(res_json['total_count']) == 0:
		return ''
	else:
		return res_json['items'][0]['login']

@login_required
def plan(request):
	teamuser = TeamUser.objects.get(email=request.user.email)
	account = teamuser.account

	return render(request, 'plan.html', {
		'teamuser': teamuser,
		'account': account,
		})

@csrf_exempt
def cancel_account(request):
	teamuser = TeamUser.objects.get(email=request.user.email)
	teamuser.account = None
	teamuser.customer_id = None
	teamuser.save()

	stripe.api_key = settings.STRIPE_KEYS['stripe_secret_key']
	subscription = stripe.Subscription.retrieve(teamuser.subscription_id)
	subscription.delete(at_period_end=True)

	return HttpResponseRedirect('/plan')

@login_required
def accept_invitation(request, m_id, t_id):
	teamuser = TeamUser.objects.get(id=m_id)
	team = Team.objects.filter(id=t_id, member=teamuser)
	if team:
		team = team[0]
		services = team.service.all()

		# send invitation for services
		for service in services:
			if service.name == 'Github':
				send_invitation_github_individual(teamuser.email, service)
			elif service.name == 'Bitbucket':
				add_member_bitbucket_individual(team.owner.email, teamuser.email, service)
			elif service.name == 'Slack':
				add_member_slack_individual(teamuser.email, service)
			else:
				pass

		return render(request, 'accept_invitation.html', {
			'teamuser': teamuser,
			'services': services,
			'team': team,
			})
	else:
		return HttpResponse('There is no such team here!')

@csrf_exempt
def create_team(request):
	team = Team()
	team.owner = request.user
	team.name = request.POST.get('team_name')
	team.save()
	return HttpResponse('success')

@csrf_exempt
def remove_service(request):
	s_id = request.POST.get('s_id')
	t_id = request.POST.get('t_id')
	team = Team.objects.get(id=t_id)
	service = Service.objects.get(id=s_id)
	team.service.remove(s_id)

	for member in team.member.all():
		if service.name == 'Github':
			delete_membership_github_individual(member.email, service)
		elif service.name == 'Bitbucket':
			delete_membership_bitbucket_individual(team.owner.email, member.email, service)

	return HttpResponse('success')


@csrf_exempt
def remove_member(request):
	m_id = request.POST.get('m_id')
	t_id = request.POST.get('t_id')
	teamuser = TeamUser.objects.get(id=m_id)
	team = Team.objects.get(id=t_id)
	team.member.remove(m_id)

	# remove all service from him
	for service in team.service.all():
		if service.name == 'Github':
			delete_membership_github_individual(teamuser.email, service)
		elif service.name == 'Bitbucket':
			delete_membership_bitbucket_individual(team.owner.email, teamuser.email, service)
		else:
			pass

	return HttpResponse('success')

@csrf_exempt
def invite_user(request):
	user_email = request.POST.get('user_email')
	t_id = request.POST.get('t_id')
	team = Team.objects.get(id=t_id)
	tusers = TeamUser.objects.filter(email=user_email)

	if tusers:
		teamuser = tusers[0]
		email_body = "Dear %s. \nYou've got an invitation from Team: %s \nYou can use all services from the team accepting the following link\n http://www.test.com/accept_invitation/%i/%i \nThank you." % (teamuser.email, team.name, teamuser.id, team.id)
	else:
		# generate temporary password
		salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
		password = hashlib.sha1(salt+user_email).hexdigest()

		teamuser = TeamUser()
		teamuser.username = user_email.split('@')[0]
		teamuser.email = user_email
		teamuser.password = make_password(password)
		teamuser.is_temp = True
		teamuser.save()

		email_body = "Dear %s. \nYou've got an invitation from Team: %s \nYou can use all services from the team accepting the following link\n http://www.test.com/accept_invitation/%i/%i \nYou can login the system with following credentials email:%s, password:%s \nOnce you login the system, please change the password as you want.  \nThank you." % (teamuser.email, team.name, teamuser.id, team.id, teamuser.email, password)

	## check he is already there
	team.member.add(teamuser)
	team.save()

	# send email
	email_subject = 'Team Invitaion'	
	send_mail(email_subject, email_body, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False)

	return HttpResponse('success')



def stripe_webhook(request):
	# Retrieve the request's body and parse it as JSON
	event_json = json.loads(request.body)

	# Verify the event by fetching it from Stripe
	event = stripe.Event.retrieve(event_json["id"])

	# print event,'#########'
	# Do something with event
	# update exp_date and handle card failures

	return HttpResponse(status=200)

def get_slug(name):
	'''
	get slug from the string
	'''
	name = name.lower()
	name = name.replace(' ', '-')
	return name
