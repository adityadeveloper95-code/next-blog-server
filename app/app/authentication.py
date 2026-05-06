from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """
    Session auth variant that returns 401 for unauthenticated requests.

    DRF chooses 401 vs 403 based on whether the authenticator provides
    a WWW-Authenticate header. Default SessionAuthentication does not,
    which leads to 403 for unauthenticated access.
    """

    def authenticate_header(self, request):
        return "Session"
