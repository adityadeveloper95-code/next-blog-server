from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def test_view(request):
    return Response({"message": "blog api is working"})
