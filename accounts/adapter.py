from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

class CustomAccountAdapter(DefaultAccountAdapter):
    def add_message(self, request, level, message_template=None, message_context=None, extra_tags='', message=None):
        # 完全不讓 allauth 自己加訊息
        pass

    def get_login_redirect_url(self, request):
        next_url = request.GET.get('next') or request.session.pop('login_next', None)
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return next_url
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return super().get_login_redirect_url(request)
