from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTest(TestCase):
    """
    Test the public available ingredients API
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """
        Test that login is required to access the endpoint
        """
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """
    Test ingredients can be retrieve by authorized user
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@singleronbio.tk',
            password='testpassword'
        )
        self.client.force_authenticate(self.user)

    def rest_retrieve_ingredient_list(self):
        """
        Test retrieving a list of ingredients
        """
        Ingredient.objects.create(user=self.user, name='ingredient 1')
        Ingredient.objects.create(user=self.user, name='ingredient 2')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """
        Test that ingredients for the authenticated user are required
        """
        user2 = get_user_model().objects.create_user(
            email='user2@singleronbio.tk',
            password='user2password'
        )
        Ingredient.objects.create(user=user2, name='user 2 ingredient')
        ingredient = Ingredient.objects.create(user=self.user, name='other ingredient')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """
        Test create a new ingredient
        """
        payload = {'name': 'create a ingredient'}
        self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """
        Test creating invalid ingredient fails
        """
        payload = {'name': ''}
        res = self.client.post(INGREDIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
