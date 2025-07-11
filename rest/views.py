# rest/views.py
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import permissions, viewsets, authentication
from rest_framework.decorators import action, authentication_classes
from rest_framework.response import Response

from .ai_service import generate_and_save_plan_for_user
# from ai_local.services import generate_and_save_local_plan_for_user as generate_and_save_plan_for_user
from .serializers import (
    FitnessPlanSerializer, UserSerializer, ProfileSerializer, EmailAuthTokenSerializer,
    WorkoutTrackingSerializer, MealTrackingSerializer
)
from .models import Profile, WorkoutTracking, MealTracking, Exercise, Meal, FitnessPlan, WorkoutDay, NutritionDay
from django.db.models import Count, Q
from datetime import datetime, date, timedelta
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
    
    
    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        """
        GET: Returns the currently authenticated user.
        PATCH/PUT: Updates the currently authenticated user's details.
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        elif request.method in ['PATCH', 'PUT']:
            # Update user details
            serializer = self.get_serializer(
                request.user, 
                data=request.data, 
                partial=request.method == 'PATCH'
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
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
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            print(f'Start date: {start_date_str}, End date: {end_date_str}')

            if not start_date_str or not end_date_str:
                return Response({"detail": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Use dateutil.parser for robust ISO 8601 parsing
                from dateutil.parser import isoparse
                start_date = isoparse(start_date_str).date()
                end_date = isoparse(end_date_str).date()
            except (ValueError, ImportError):
                # Fallback or error for invalid format
                return Response({"detail": "Invalid date format. Use ISO 8601 format."}, status=status.HTTP_400_BAD_REQUEST)

            # Check for overlapping plans
            overlapping_plans = FitnessPlan.objects.filter(
                profile=profile,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping_plans.exists():
                return Response({"detail": "A plan already exists for the selected date range."}, status=status.HTTP_400_BAD_REQUEST)


            # IMPORTANT: This is a long-running task.
            # In production, this should be offloaded to a background worker (e.g., Celery).
            plan = generate_and_save_plan_for_user(profile, start_date, end_date)
            if plan:
                serializer = FitnessPlanSerializer(plan)
                return Response({
                    "message": "Fitness plan generated successfully.",
                    "plan": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({"detail": "Failed to generate fitness plan."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], url_path='me/plans')
    def delete_plan(self, request, pk=None):
        """
        Delete a fitness plan for the authenticated user.
        """
        print('got here')
        try:
            plan = FitnessPlan.objects.get(pk=pk, profile__user=request.user)
            plan.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FitnessPlan.DoesNotExist:
            return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/workout-tracking')
    def workout_tracking(self, request):
        """
        GET: Retrieve workout tracking records for the authenticated user.
        POST: Create a new workout tracking record.
        DELETE: Delete a workout tracking record.
        """
        if request.method == 'GET':
            date = request.query_params.get('date')
            queryset = WorkoutTracking.objects.filter(user=request.user)
            if date:
                queryset = queryset.filter(date_completed=date)
            queryset = queryset.order_by('-date_completed')
            
            serializer = WorkoutTrackingSerializer(queryset, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = WorkoutTrackingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            tracking_id = request.data.get('id')
            if not tracking_id:
                return Response({"detail": "Tracking record ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                tracking_record = WorkoutTracking.objects.get(pk=tracking_id, user=request.user)
                tracking_record.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except WorkoutTracking.DoesNotExist:
                return Response({"detail": "Tracking record not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get', 'post', 'delete'], url_path='me/meal-tracking')
    def meal_tracking(self, request):
        """
        GET: Retrieve meal tracking records for the authenticated user.
        POST: Create a new meal tracking record.
        DELETE: Delete a meal tracking record.
        """
        if request.method == 'GET':
            date = request.query_params.get('date')
            queryset = MealTracking.objects.filter(user=request.user)
            if date:
                queryset = queryset.filter(date_completed=date)
            queryset = queryset.order_by('-date_completed')
            
            serializer = MealTrackingSerializer(queryset, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data['user'] = request.user.id
            serializer = MealTrackingSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        elif request.method == 'DELETE':
            tracking_id = request.data.get('id')
            if not tracking_id:
                return Response({"detail": "Tracking record ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                tracking_record = MealTracking.objects.get(pk=tracking_id, user=request.user)
                tracking_record.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except MealTracking.DoesNotExist:
                return Response({"detail": "Tracking record not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='me/daily-progress')
    def daily_progress(self, request):
        """
        GET: Calculate daily progress for workout and nutrition for a specific date or date range.
        Query params:
        - date: specific date (YYYY-MM-DD)
        - start_date: start of date range (YYYY-MM-DD)
        - end_date: end of date range (YYYY-MM-DD)
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get active fitness plan
        active_plan = profile.fitness_plans.filter(is_active=True).first()
        if not active_plan:
            return Response({"detail": "No active fitness plan found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse date parameters
        date_param = request.query_params.get('date')
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')
        
        if date_param:
            # Single date
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                dates = [target_date]
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        elif start_date_param and end_date_param:
            # Date range
            try:
                start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
                dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to today
            dates = [date.today()]
        
        progress_data = []
        
        for target_date in dates:
            # Calculate day of week (1=Monday, 7=Sunday)
            day_of_week = target_date.isoweekday()
            
            # Get planned workouts for this day
            workout_day = active_plan.workout_days.filter(day_of_week=day_of_week).first()
            workout_progress = 0
            
            if workout_day and not workout_day.is_rest_day:
                total_exercises = workout_day.exercises.count()
                if total_exercises > 0:
                    completed_exercises = WorkoutTracking.objects.filter(
                        user=request.user,
                        date_completed=target_date,
                        exercise__workout_day=workout_day
                    ).count()
                    workout_progress = (completed_exercises / total_exercises) * 100
            elif workout_day and workout_day.is_rest_day:
                workout_progress = 100  # Rest days are always "complete"
            
            # Get planned meals for this day
            nutrition_day = active_plan.nutrition_days.filter(day_of_week=day_of_week).first()
            nutrition_progress = 0
            
            if nutrition_day:
                total_meals = nutrition_day.meals.count()
                if total_meals > 0:
                    completed_meals = MealTracking.objects.filter(
                        user=request.user,
                        date_completed=target_date,
                        meal__nutrition_day=nutrition_day
                    ).count()
                    nutrition_progress = (completed_meals / total_meals) * 100
            
            progress_data.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'day_of_week': day_of_week,
                'workout_progress': round(workout_progress, 1),
                'nutrition_progress': round(nutrition_progress, 1),
                'is_rest_day': workout_day.is_rest_day if workout_day else False
            })
        
        return Response({
            'progress': progress_data
        })

# a status view

class StatusView(APIView):
    """
    A simple view to check the status of the API.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        """
        Returns a simple status message.
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

