# rest/views.py
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions, viewsets, authentication
from rest_framework.decorators import action, authentication_classes
from rest_framework.response import Response

from .ai_service import generate_and_save_plan_for_user
from .serializers import FitnessPlanSerializer, UserSerializer, ProfileSerializer, EmailAuthTokenSerializer
from .models import Profile
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status, generics # Make sure to import status





from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

class LoginView(generics.GenericAPIView):
    """
    Custom login view that authenticates with email and returns token + user.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        """Handles POST requests to authenticate a user and return a token.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

class SignUpView(generics.GenericAPIView):
    """
    Custom signup view that allows user registration and returns token + user.
    """
    queryset = User.objects.all()
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """Handles POST requests to register a new user and return a token.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)



class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'me_profile':
            return ProfileSerializer
        return super().get_serializer_class()
    
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    

    @action(detail=False, methods=['get', 'post', 'put', 'patch'], url_path='me/profile')
    def me_profile(self, request, pk=None):
        """
        Retrieve, create, or update the profile for the currently authenticated user.
        """
        # Try to get the profile, handle if it doesn't exist.
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = None

        if request.method == 'GET':
            if not profile:
                return Response({"message": "Profile not found. Please create one by sending a POST request."}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        elif request.method == 'POST':
            if profile:
                return Response({"message": "Profile already exists. Use PUT or PATCH to update."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Use the serializer to validate and create
            serializer = ProfileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # Pass the user in the .save() method, DRF handles the association
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method in ['PUT', 'PATCH']:
            if not profile:
                return Response({"message": "Profile not found. Please create one first."}, status=status.HTTP_404_NOT_FOUND)
            
            # Use the serializer to validate and update
            # partial=True allows for partial updates with PATCH
            serializer = ProfileSerializer(profile, data=request.data, partial=request.method == 'PATCH')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'], url_path='me/plans')
    def me_plans(self, request):
        """
        GET: Retrieve fitness plans for the authenticated user.
        POST: Generate a new fitness plan for the authenticated user.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found. Please create a profile first."}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            plans = profile.fitness_plans.all()
            serializer = FitnessPlanSerializer(plans, many=True)
            return Response(serializer.data)
        
        if request.method == 'POST':
            # IMPORTANT: This is a long-running task.
            # In production, this should be offloaded to a background worker (e.g., Celery).
            plan = generate_and_save_plan_for_user(profile)
            if plan:
                serializer = FitnessPlanSerializer(plan)
                return Response({
                    "message": "Fitness plan generated successfully.",
                    "plan": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"detail": "Failed to generate fitness plan."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


