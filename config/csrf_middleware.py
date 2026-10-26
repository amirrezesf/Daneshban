from django.middleware.csrf import _unmask_cipher_token

class IframeCsrfCookieMiddleware:
    """
    Middleware ensuring that in cross-origin preview iframes (such as Google AI Studio),
    where browsers may partition or restrict 3rd-party cookies, CSRF tokens embedded
    in forms are still recognized by Django even if the browser blocked the initial cookie.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and "csrftoken" not in request.COOKIES:
            post_token = request.POST.get("csrfmiddlewaretoken") or request.headers.get("x-csrftoken")
            if post_token and len(post_token) in (32, 64):
                try:
                    if len(post_token) == 64:
                        request.COOKIES["csrftoken"] = _unmask_cipher_token(post_token)
                    else:
                        request.COOKIES["csrftoken"] = post_token
                except Exception:
                    pass

        response = self.get_response(request)
        return response
