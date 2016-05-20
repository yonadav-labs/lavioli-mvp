from django import template
from django.template import Template

from team.models import *

register = template.Library()


@register.simple_tag(takes_context=True)
def team_menu(context, format):
    """
    Return a list of child menus containing the teams the user owned
    """
    request = context["request"]
    teams = Team.objects.filter(owner=request.user)
    render_menu = ''
    for team in teams:
        render_menu = render_menu + '<li><a href="/team/%i">%s <span class="glyphicon glyphicon-flag"></span></a></li>' % (team.id, team.name)

    return render_menu

@register.simple_tag(takes_context=True)
def myteam_menu(context, format):
    """
    Return a list of child menus containing the teams the user belongs into
    """
    request = context["request"]
    teams = Team.objects.filter(member=request.user)
    render_menu = ''
    for team in teams:
        render_menu = render_menu + '<li><a href="/myteam/%i">%s <span class="glyphicon glyphicon-flag"></span></a></li>' % (team.id, team.name)

    return render_menu
