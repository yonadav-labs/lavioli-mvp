import hashlib, datetime, random
import stripe
from datetime import timedelta

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import *

from .models import *


stripe_keys = {
    'stripe_secret_key': 'sk_test_1AFSPD5Dg8RihyPPtylWiSsR',
    'publishable_key': 'pk_test_Q4RGBzPFhWbMP2daCqMg6Rj7'
}


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
	team = Team.objects.get(id=id)
	members = team.member.all()
	services = team.service.all()
	return render(request, 'myteam_info.html', {
		'team': team,
		'members': members,
		'services': services,
		})

@login_required
def add_service(request, id):
	team = Team.objects.get(id=id)
	services = team.service.all()
	services = [service.id for service in services]
	other_services = Service.objects.all().exclude(id__in=services)
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
		'key': stripe_keys['publishable_key'],
		})

@login_required
def charge_account(request):
	teamuser = TeamUser.objects.get(email=request.user.email)
	a_id = request.POST.get('a_id')
	account = Account.objects.get(id=a_id)
	teamuser.account = account
	teamuser.exp_date = datetime.date.today() + timedelta(days=30)
	teamuser.save()

	card = request.POST.get('stripeToken')

	stripe.api_key = stripe_keys['stripe_secret_key']
	customer = stripe.Customer.create(
		email=teamuser.email,
		card=card
	)

	charge = stripe.Charge.create(
		customer=customer.id,
		amount=account.budget*100,
		currency='usd',
		description='MVP Charge'
	)

	teamuser.last4_card_num = charge.source.last4
	teamuser.save()

	return HttpResponseRedirect('/plan')

@login_required
def add_service_real(request, s_id, t_id):
	team = Team.objects.get(id=t_id)
	service = Service.objects.get(id=s_id)
	team.service.add(service)
	team.save()

	return HttpResponseRedirect('/team/'+t_id)

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
	teamuser.save()
	
	# remove periodic payment.
	return HttpResponseRedirect('/plan')

@login_required
def accept_invitation(request, m_id, t_id):
	teamuser = TeamUser.objects.get(id=m_id)
	team = Team.objects.filter(id=t_id, member=teamuser)
	if team:
		team = team[0]
		services = team.service.all()
		return render(request, 'accept_invitation.html', {
			'teamuser': teamuser,
			'services': services,
			'team': team,
			})

	else:
		return HttpResponse('There is no such team here!')

	service = Service.objects.get(id=s_id)
	team.service.add(service)
	team.save()

	return HttpResponseRedirect('/team/'+t_id)

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
	team.service.remove(s_id)
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
		# generate temperary password
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

