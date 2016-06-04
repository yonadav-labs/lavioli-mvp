from django import forms
	
class GithubForm(forms.Form):
    name = forms.CharField()
    token = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Token')
    org_name = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Organization Name')
    team_name = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Team Name')

class BitbucketForm(forms.Form):
    name = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput(attrs={'required': True, 'class': 'form-control'}), label='Password on Bitbucket')
    group_name = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Group Name')

class SlackForm(forms.Form):
    name = forms.CharField()
    team_token = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Team Token')
