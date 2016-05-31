from django import forms
	
class GithubForm(forms.Form):
    name = forms.CharField()
    token = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Token')
    org_name = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Organization Name')
    team_name = forms.CharField(widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}), label='Team Name')

