from django.contrib.auth.models import Group
from rest_framework import serializers
from rest.models import Profile, User # Assuming Profile is defined in rest/models.py


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


