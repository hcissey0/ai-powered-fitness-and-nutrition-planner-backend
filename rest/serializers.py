# rest/serializers.py

from django.contrib.auth.models import Group
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import (
    Exercise, FitnessPlan,
    Meal, NutritionDay,
    Profile, WorkoutDay
)

User = get_user_model()



class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not (email and password):
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        except User.DoesNotExist:
            msg = _('A user with this email does not exist.')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs




        
        



class ProfileSerializer(serializers.ModelSerializer):
    # This nested serializer is great for GET requests.
    # user = UserSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    # user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # This calculated field is perfect.
    bmi = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'current_weight', 'height', 'age', 'gender', 
            'activity_level', 'goal', 'dietary_preferences', 'image',
            'bmi', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_bmi(self, obj):
        # This logic is correct. It will return None if data is missing.
        return obj.bmi

class UserSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'first_name', 'last_name', 'is_active', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'email': {'required': True}
            }
        read_only_fields = ['id', 'date_joined', 'is_active']
        
        ordering = ['date_joined']

    def validate_email(self, value):
        """
        Check if the email is already in use.
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'


class WorkoutDaySerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutDay
        fields = '__all__'


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = '__all__'


class NutritionDaySerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)

    class Meta:
        model = NutritionDay
        fields = '__all__'


class FitnessPlanSerializer(serializers.ModelSerializer):
    workout_days = WorkoutDaySerializer(many=True, read_only=True)
    nutrition_days = NutritionDaySerializer(many=True, read_only=True)

    class Meta:
        model = FitnessPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']



