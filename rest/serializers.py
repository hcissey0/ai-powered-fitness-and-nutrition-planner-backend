from django.contrib.auth.models import Group
from rest_framework import serializers
from rest.models import FitnessPlan, Profile # Assuming Profile is defined in rest/models.py


# serializers.py
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                msg = _('A user with that email does not exist.')
                raise serializers.ValidationError(msg, code='authorization')
            # user = authenticate(request=self.context.get('request'), email=email, password=password)
            # if not user:
            #     msg = _('Unable to log in with provided credentials.')
            #     raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs



class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'profile', 'first_name', 'last_name', 'is_active', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}
        depth = 1  # Adjust depth as needed for nested serialization
        read_only_fields = ['id', 'date_joined', 'is_active']
        
        ordering = ['date_joined']
        
        


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Assuming a OneToOne relationship with User
    # user = serializers.PrimaryKeyRelatedField(read_only=True)  # Assuming a OneToOne relationship with User

    def create(self, validated_data):
        profile = Profile.objects.create( **validated_data)
        return profile

    def update(self, instance, validated_data):
        instance.current_weight = validated_data.get('current_weight', instance.current_weight)
        instance.height = validated_data.get('height', instance.height)
        instance.age = validated_data.get('age', instance.age)
        instance.weight = validated_data.get('weight', instance.weight)
        instance.activity_level = validated_data.get('activity_level', instance.activity_level)
        instance.goal = validated_data.get('goal', instance.goal)
        # Assuming bmi is calculated based on other fields, you might want to handle that here
        # For example, if height and weight are provided, calculate bmi
        if instance.height and instance.weight:
            height_meters = instance.height / 100.0
            instance.bmi = instance.weight / (height_meters ** 2)
        else:
            instance.bmi = None
        instance.save()
        return instance

    class Meta:
        model = Profile  # Assuming you have a OneToOne relationship with Profile
        # fields = ['user', 'current_weight', 'height', 'bmi', 'age', 'weight', 'activity_level', 'goal']
        fields = '__all__'
        read_only_fields = ['bmi', 'id']  # Assuming bmi is calculated and not set dir
        depth = 1  # Adjust depth as needed for nested serialization

class FitnessPlanSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = FitnessPlan  # Assuming you have a FitnessPlan model
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
        depth = 5  # Adjust depth as needed for nested serialization


