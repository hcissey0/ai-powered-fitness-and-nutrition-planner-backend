from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, authentication
from rest_framework.decorators import action
from rest_framework.response import Response


from .serializers import UserSerializer, ProfileSerializer
from .models import Profile
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Returns the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)



class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing profile instances.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class AuthToken(ObtainAuthToken):
    """
    Custom authentication token view to return user data along with the token.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})