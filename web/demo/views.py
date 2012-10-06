from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

@login_required
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')