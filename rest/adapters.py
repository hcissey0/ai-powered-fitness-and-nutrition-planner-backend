# rest/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field
from django.contrib.auth import get_user_model
from .models import Profile
from django.utils.text import slugify

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def new_user(self, request, sociallogin):
        return super().new_user(request, sociallogin)

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a new user instance when a user signs up via a social account.
        """
        user = super().save_user(request, sociallogin, form)

        try:
            user_data = sociallogin.account.extra_data
            first_name = user_data.get('given_name', '') or user_data.get('first_name', '')
            last_name = user_data.get('family_name', '') or user_data.get('last_name', '')

            # Auto-generate username if missing
            if not user.username:
                email = user.email or user_data.get('email', '')
                base_username = slugify(email.split('@')[0]) if email else f"user_{user.id}"
                user.username = base_username

            # Populate first and last name if missing
            if first_name and not user.first_name:
                user.first_name = first_name
            if last_name and not user.last_name:
                user.last_name = last_name

            user.save()

            # Ensure Profile exists
            # Profile.objects.get_or_create(user=user)

        except Exception as e:
            print(f"Error populating user details from social account: {e}")

        return user
