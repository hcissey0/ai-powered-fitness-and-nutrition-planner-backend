from django.contrib.auth.models import User
from django.contrib.auth import authenticate
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


class LoginAuthView(ObtainAuthToken):
    """
    Custom auth view that authenticates with email and returns token + user.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = EmailAuthTokenSerializer
    

    def post(self, request, *args, **kwargs):
        """Handles POST requests to authenticate a user and return a token.
        """
        email = request.data.get('email', None)
        if not email:
            return Response({"error": "Email is required."}, status=400)
        password = request.data.get('password', None)
        if not password:
            return Response({"error": "Password is required."}, status=400)
        
        # user = authenticate(request, email=email, password=password)
        # if not user:
        #     return Response({"error": "Invalid credentials."}, status=400)

        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

class SignUpAuthView(ObtainAuthToken):
    """
    Custom auth view that allows user registration and returns token + user.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """Handles POST requests to register a new user and return a token.
        """
        print('request.data:', request.data)
        print('request.data.get("first_name"):', request.data.get('first_name', ''))
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        username = request.data.get('username', None)
        if not username:
            username = first_name + last_name + str(User.objects.count() + 1)
        print('username:', username)
        email = request.data.get('email', None)
        if not email:
            return Response({"error": "Email is required."}, status=400)
        print('email:', email)
        password = request.data.get('password', None)
        if not password:
            return Response({"error": "Password is required."}, status=400)
        print('password:', password)
        emailAvail = User.objects.filter(email=request.data.get('email')).exists()
        if emailAvail:
            return Response({"error": "Email already exists."}, status=400)
        print('emailAvail:', emailAvail)
        usernameAvail = User.objects.filter(username=username).exists()
        if usernameAvail:
            return Response({"error": "Username already exists."}, status=400)
        
        user = User.objects.create(first_name=first_name, 
                                   last_name=last_name, username=username, email=email)

        user.set_password(password)  # Hash the password
        user.save()
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
        return [permissions.IsAuthenticated()]
        

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'post'], url_path='me/profile')
    def me_profile(self, request, pk=None):
        """
        Returns the profile of the currently authenticated user.
        """
        if request.method == 'POST':
            # Handle profile creation or update
            serializer = ProfileSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            profile = serializer.save(user=request.user)
            return Response(ProfileSerializer(profile).data, status=201)
        elif request.method == 'GET':
            # Handle profile retrieval
            if not hasattr(request.user, 'profile'):
                return Response({"message": "Profile not found."}, status=404)
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

    
    @action(detail=False, methods=['get', 'post'], url_path='me/plans')
    def me_plans(self, request, pk=None):
        """
        Placeholder for a custom action to generate a fitness plan.
        """
        if not request.user.profile:
            return Response({"message": "Profile not found. Please create a profile first."}, status=404)
        if request.method == 'POST':
            plan = generate_and_save_plan_for_user(request.user.profile)
            if plan:
                return Response({"message": "Fitness plan generated successfully.", "plan": FitnessPlanSerializer(plan).data}, status=201)
            else:
                return Response({"message": "Failed to generate fitness plan."}, status=500)
        elif request.method == 'GET':
            fitness_plans = FitnessPlanSerializer(request.user.profile.fitness_plans.all(), many=True)
            return Response(fitness_plans.data, status=200)
        return Response({"message": "Method not allowed."}, status=405)

    # @plans.mapping.get
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