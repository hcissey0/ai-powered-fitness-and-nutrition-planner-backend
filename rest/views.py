from django.contrib.auth.models import User
from rest_framework import permissions, viewsets, authentication
from rest_framework.decorators import action, authentication_classes
from rest_framework.response import Response

from .googleai import generate_and_save_plan_for_user
from .serializers import FitnessPlanSerializer, UserSerializer, ProfileSerializer, EmailAuthTokenSerializer
from .models import Profile
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token


# views.py



from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class AuthToken(ObtainAuthToken):
    """
    Custom auth view that authenticates with email and returns token + user.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })




class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


    def get_permissions(self):
        if self.action == 'create':
            # Allow any user to create a new user
            return [AllowAny()]
        else: 
            # For other actions, require authentication
            return super().get_permissions()
        

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """
        Returns the profile of the currently authenticated user.
        """
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    @action( detail=False, methods=['post'], url_path='me/plans')
    def plans(self, request, pk=None):
        """
        Placeholder for a custom action to generate a fitness plan.
        """
        plan = generate_and_save_plan_for_user(request.user.profile)
        if plan:
            return Response({"message": "Fitness plan generated successfully.", "plan": FitnessPlanSerializer(plan).data}, status=201)
        else:
            return Response({"message": "Failed to generate fitness plan."}, status=500)
        # return Response({"message": "This is where the fitness plan generation logic will go."})

    @plans.mapping.get
    def get_plans(self, request, pk=None):
        """
        Returns the fitness plan for the authenticated user.
        """
        profile = request.user.profile
        if not profile.fitness_plans:
            return Response({"message": "No fitness plan found for this user."}, status=404)
        
        res = [FitnessPlanSerializer(plan).data for plan in profile.fitness_plans.all()]
        # serializer = FitnessPlanSerializer(profile.fitness_plan)
        return Response(res, status=200)


class ProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing profile instances.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        profile = Profile.objects.create(user=user, **request.data)
        ser_profile = self.get_serializer(profile)
        return ser_profile


# class AuthToken(ObtainAuthToken):
#     """
#     Custom authentication token view to return user data along with the token.
#     """
#     authentication_classes = []
#     permission_classes = [permissions.AllowAny]
#     serializer_class = UserSerializer
#     def post(self, request, *args, **kwargs):
#         """"Handles POST requests to authenticate a user and return a token.
#         """
#         print(request.data)
#         serializer = self.serializer_class(data=request.data,
#                                            context={'request': request})
        
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({'token': token.key, 'user': UserSerializer(user).data})