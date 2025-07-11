from django.test import TestCase
from unittest.mock import patch, MagicMock
from .services import LocalModel, get_local_model, generate_and_save_local_plan_for_user


class LocalModelTests(TestCase):
    
    @patch('ai_local.services.LLAMA_CPP_AVAILABLE', False)
    def test_model_without_llama_cpp(self):
        """Test that model gracefully handles missing llama-cpp-python"""
        model = LocalModel('/fake/path/model.gguf')
        self.assertIsNone(model.model)
    
    @patch('ai_local.services.os.path.exists')
    def test_model_with_missing_file(self, mock_exists):
        """Test that model handles missing model file"""
        mock_exists.return_value = False
        model = LocalModel('/fake/path/model.gguf')
        self.assertIsNone(model.model)
    
    def test_fallback_plan_generation(self):
        """Test that fallback plan generation works"""
        model = LocalModel('/fake/path/model.gguf')
        plan_json = model._generate_fallback_plan()
        
        import json
        plan_data = json.loads(plan_json)
        
        # Check structure
        self.assertIn('workout_days', plan_data)
        self.assertIn('nutrition_days', plan_data)
        self.assertEqual(len(plan_data['workout_days']), 7)
        self.assertEqual(len(plan_data['nutrition_days']), 7)
        
        # Check workout day structure
        workout_day = plan_data['workout_days'][0]
        self.assertIn('day_of_week', workout_day)
        self.assertIn('title', workout_day)
        self.assertIn('exercises', workout_day)
        
        # Check nutrition day structure
        nutrition_day = plan_data['nutrition_days'][0]
        self.assertIn('day_of_week', nutrition_day)
        self.assertIn('meals', nutrition_day)
        self.assertIn('target_calories', nutrition_day)


class AiLocalIntegrationTests(TestCase):
    
    def setUp(self):
        from django.contrib.auth.models import User
        from rest.models import Profile
        
        # Create test user and profile
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile = Profile.objects.create(
            user=self.user,
            age=25,
            gender='M',
            current_weight=70,
            height=175,
            goal='weight_loss',
            activity_level='moderate'
        )
    
    @patch('ai_local.services.get_local_model')
    def test_plan_generation_with_fallback(self, mock_get_model):
        """Test plan generation using fallback when model fails"""
        # Mock a failed model
        mock_model = MagicMock()
        mock_model.model = None
        mock_model.generate_plan.return_value = mock_model._generate_fallback_plan()
        mock_get_model.return_value = mock_model
        
        plan = generate_and_save_local_plan_for_user(self.profile)
        
        # Should still create a plan even with fallback
        self.assertIsNotNone(plan)
        self.assertEqual(plan.profile, self.profile)
