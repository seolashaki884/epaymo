from django.shortcuts import render
from django.http import Http404

class Custom404Middleware:
    """
    Custom middleware to display a custom 404 page for not found errors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # If the response is a 404 error, show a custom page
        if response.status_code == 404:
            return render(request, 'core/404.html', {}, status=404)

        return response