from django import forms
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.messages.api import get_messages
from django.contrib import auth
from django.contrib.auth.models import User

from social_auth import __version__ as version

def _setting(name, default=''):
    return getattr(settings, name, default)

SESSION_USER_NAME = _setting('SOCIAL_AUTH_SESSION_USER_NAME', 'tmp_social_auth')

def home(request):
    """Home view, displays login mechanism"""
    if request.user.is_authenticated():
        return HttpResponseRedirect('done')
    else:
        return render_to_response('home.html', {'version': version},
                                  RequestContext(request))

@login_required
def done(request):
    """Login complete view, displays user data"""
    ctx = {'version': version,
           'last_login': request.session.get('social_auth_last_login_backend')}
    return render_to_response('done.html', ctx, RequestContext(request))

def error(request):
    """Error view"""
    messages = get_messages(request)
    return render_to_response('error.html', {'version': version,
                                             'messages': messages},
                              RequestContext(request))

def logout(request):
    """Logs out user"""
    auth_logout(request)
    return HttpResponseRedirect('/')

attrs_dict = {'class': 'required'}

class RegistrationFormBase(forms.Form):
    username = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)), label=_("Email address"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False), label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False), label=_("Password (again)"))
    
    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            self.cleaned_data['email'] = self.cleaned_data['username']
            return self.cleaned_data['username']
        raise forms.ValidationError(_("A user with that username already exists."))

    def clean(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data
    
class UserReginstrationFormShort(RegistrationFormBase):
    pass

class LoginForm(forms.Form):
    username = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)), label=_("Email address"))
    password = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False), label=_("Password"))

def login_with_linked_social_user(request):
    # todo: get social user
    
    #social_user = request.session[SESSION_USER_NAME] 
    #return render_to_response('login_with_social.html',{'social_user':social_user},RequestContext(request))
    if not SESSION_USER_NAME in request.session:
        return HttpResponseRedirect('/')
     
    social_user = request.session[SESSION_USER_NAME]
    social_profile = social_user.profile 
    if request.method == 'POST':
        if 'login' == request.META['QUERY_STRING']:
            login_form = LoginForm(request.POST) 
            if login_form.is_valid():
                auth_user = auth.authenticate(username=login_form.cleaned_data['username'], password=login_form.cleaned_data['password'])
                if auth_user:
                    auth.login(request, auth_user)
                    social_user.user = auth_user
                    social_user.save()
                    return HttpResponseRedirect('/')
            return render_to_response('login_with_social.html', {'social_user': social_user, 'registration_form':UserReginstrationFormShort(), 
                                                                         'login_form':login_form},
                                              RequestContext(request))
        elif 'create' == request.META['QUERY_STRING']:
            registration_form = UserReginstrationFormShort(request.POST)
            if registration_form.is_valid():
                
                new_user = User.objects.create_user(registration_form.cleaned_data['username'], registration_form.cleaned_data['username'], registration_form.cleaned_data['password1'])
                new_user.is_active = True
                new_user.save()
                
                social_user.user = new_user
                social_user.save()
                
                if social_profile:
                    session_profile = social_profile
                    session_profile.user = new_user
                    session_profile.save()
                
                auth_user = auth.authenticate(username=registration_form.cleaned_data['username'], password=registration_form.cleaned_data['password1'])
                auth.login(request, auth_user)
                return HttpResponseRedirect('/')
            else:
                return render_to_response('login_with_social.html', {'social_user': social_user, 'login_form':LoginForm(), 
                                                                             'registration_form':registration_form},RequestContext(request))
    
    return render_to_response('login_with_social.html', {'social_user': social_user, 'login_form':LoginForm(), 
                                                                 'registration_form':UserReginstrationFormShort()},RequestContext(request))
