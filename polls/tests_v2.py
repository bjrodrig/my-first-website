import datetime
from freezegun import freeze_time

from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse




from django.db.models import Count
from unittest.mock import patch, MagicMock

from .models import UserProfileForm, UserProfile, UserDays, RememberMeals, UserMeals, FoodDatabase, FoodDatabaseForm
from .views import *
from .forms import PersonalMealsForm, MultipleMealsForm
from .forms import SignUpForm, UserMealsForm, QuickAddForm, RememberMealsForm
from polls import views

from .tests import create_food_database_objects

class RememberMealsTest(TestCase):

	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		self.factory = RequestFactory()
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 13), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		UserDays.objects.create(user=user, date=datetime.date(2017, 5, 31), done=False)
		create_food_database_objects()
		banana = FoodDatabase.objects.get(food="Banana")
		fiber_bar = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(banana, 1, "banana", "B", 3, "2017-05-31", user, 3)
		create_database_record(fiber_bar, 1, "ounce", "B", 1.4175, "2017-05-31", user, 2)
		half_and_half = FoodDatabase.objects.get(food='Half and Half')
		create_database_record(half_and_half, 1, "TBSP", "S", 2, "2017-05-31", user, 2)
		RememberMeals.objects.create(title="ThisMeal", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=fiber_bar, portion=1, units_consumed=40,
									 units="grams", cal_eaten=140, carbs=29, fat=4, protein=2, sodium=90,
									 sugar=10)
		
	def test_remember_meals_redirect(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/Remember Meal/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/remember_meal.html")
		
	def test_remember_meal_template(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/Remember Meal/quicktools_options/", follow=True)
		self.assertContains(response, "Banana")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "3.0 bananas")
		self.assertContains(response, "2.0 ounces")
		self.assertContains(response, "528")
		self.assertContains(response, "<b>Name this meal</b>")
		self.assertContains(response, "Title")
		self.assertNotContains(response, "Half and Half")
	
	
		
	def test_status_code_get_remember_meals(self):
		request = self.factory.get("/polls/2017-05-31/Breakfast/remember_meal_func/", follow=True)
		request.user = self.user
		response = remember_meal_func(request, "Breakfast", "2017-05-31")
		self.assertEqual(response.status_code, 200)
		
	def test_post_remember_meals_form(self):
		form_data = {'title': 'ThisMealv3'}
		
		request = self.factory.post("/polls/2017-05-31/Breakfast/remember_meal_func/", form_data, follow=True)
		request.user = self.user
		
		form_data['title'] = 'ThisMealv4'
		form = RememberMealsForm(request=request, data=form_data)
		response = remember_meal_func(request, "Breakfast", "2017-05-31")
		self.assertTrue(form.is_valid())
		self.assertEqual(response.status_code, 302)
		
	def test_invalid_form(self):
		form_data = {'title': 'ThisMealv5'}
		
		request = self.factory.post("/polls/2017-05-31/Breakfast/remember_meal_func/", form_data, follow=True)
		request.user = self.user
		
		form_data['title'] = 'ThisMeal'
		form = RememberMealsForm(request=request, data=form_data)
		response = remember_meal_func(request, "Breakfast", "2017-05-31")
		self.assertFalse(form.is_valid())
		self.assertEqual(response.status_code, 302)
		
	def test_form_title_same_but_different_capitalization(self):
		form_data = {'title': 'ThisMealv5'}
		
		request = self.factory.post("/polls/2017-05-31/Breakfast/remember_meal_func/", form_data, follow=True)
		request.user = self.user
		
		form_data['title'] = 'Thismeal'
		form = RememberMealsForm(request=request, data=form_data)
		response = remember_meal_func(request, "Breakfast", "2017-05-31")
		self.assertTrue(form.is_valid())
		self.assertEqual(response.status_code, 302)
		
	def test_remember_meal_model_created(self):
		form_data = {'title': 'ThisMealv6'}
		request = self.client.post("/polls/2017-05-31/Breakfast/remember_meal_func/", form_data, follow=True)
		get_remembered_meal = RememberMeals.objects.filter(user=self.user, title="ThisMealv6")
		count_meals = get_remembered_meal.count()
		self.assertEqual(count_meals, 2)
		meal_1 = get_remembered_meal[0]
		meal_2 = get_remembered_meal[1]
		self.assertEqual(meal_1.title, "ThisMealv6")
		self.assertEqual(meal_2.title, "ThisMealv6")
		banana = FoodDatabase.objects.get(food="Banana")
		fiber_bar = FoodDatabase.objects.get(food="Fiber One Bar")
		self.assertEqual(meal_1.food_item, banana)
		self.assertEqual(meal_2.food_item, fiber_bar)
		self.assertTemplateUsed("polls/food.html")
		self.assertNotContains(request, "Close")
		
class AddFoodToDatabaseTest(TestCase):

	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		self.factory = RequestFactory()
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')
		create_food_database_objects()
		
		
	def update_add_food_form(self, category, result):
		form_data = {
			'food': 'Carrot',
			'calories': 30,
			'carbs': 0,
			'fat': 0,
			'protein': 0,
			'sodium': 0,
			'sugar': 0,
			'serving_size': 1,
			'units': 'carrot'
		}
		form_data[category] = result
		return form_data
		
	def test_add_food_to_database_get_template(self):
		response = self.client.get("/polls/add_food_to_database/", follow=True)
		self.assertTemplateUsed("polls/add_food_to_database.html")
		self.assertContains(response, "If added, must be in grams.")
		self.assertContains(response, "If added, must be in milligrams.")
		
	def test_add_food_form(self):
		# start wtih valid form, set carbs, fat, protein, sodium, sugar to null, which should pass
		form_data = self.update_add_food_form("food", "Carrot")
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_food_character(self):
		# food is none
		form_data = self.update_add_food_form("food", "")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		form_data = self.update_add_food_form("food", .2)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		#name already exists (see SetUP)
		form_data = self.update_add_food_form("food", "Banana")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_calories(self):
		# word is not valid
		form_data = self.update_add_food_form("calories", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is .1
		form_data = self.update_add_food_form("calories", .1)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
		#0 is not valid
		form_data = self.update_add_food_form("calories", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#test blank
		form_data = self.update_add_food_form("calories", None)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_carbs(self):
		# word is not valid
		form_data = self.update_add_food_form("carbs", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("carbs", -.1)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("carbs", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_fat(self):
		# word is not valid
		form_data = self.update_add_food_form("fat", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("fat", -.1)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("fat", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_protein(self):
		# word is not valid
		form_data = self.update_add_food_form("protein", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("protein", -.1)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("protein", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_sodium(self):
		# word is not valid
		form_data = self.update_add_food_form("sodium", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("sodium", -.1)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("sodium", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_sugar(self):
		# word is not valid
		form_data = self.update_add_food_form("sugar", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("sugar", -.1)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("sugar", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_serving_size(self):
		# word is not valid
		form_data = self.update_add_food_form("serving_size", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#min value is 0
		form_data = self.update_add_food_form("serving_size", 0)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		form_data = self.update_add_food_form("serving_size", .1)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
		#test blank field
		form_data = self.update_add_food_form("serving_size", None)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_units(self):
		# word is valid
		form_data = self.update_add_food_form("units", "hello")
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
		#test blank
		form_data = self.update_add_food_form("units", None)
		form = FoodDatabaseForm(data=form_data)
		self.assertFalse(form.is_valid())
		
		#number should pass
		form_data = self.update_add_food_form("units", .1)
		form = FoodDatabaseForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_database_object_created(self):
		form_data = self.update_add_food_form("food", "carrot")
		response = self.client.post("/polls/add_food_to_database/", form_data, follow=True)
		#carrot record should have been created
		get_food = FoodDatabase.objects.filter(food="carrot").count()
		# assert one carrot record was created
		self.assertEqual(get_food, 1)
		
	def test_success_template(self):
		form_data = self.update_add_food_form("food", "carrot")
		response = self.client.post("/polls/add_food_to_database/", form_data, follow=True)
		self.assertTemplateUsed("polls/success.html")
		self.assertContains(response, "Food was successfuly added to the database.")
		
	def test_post_invalid_form(self):
		form_data = self.update_add_food_form("food", "")
		response = self.client.post("/polls/add_food_to_database/", form_data, follow=True)
		self.assertNotContains(response, "Food was successfuly added to the database.")
		self.assertContains(response, "If added, must be in grams.")
		get_meal = FoodDatabase.objects.filter(food="").count()
		self.assertEqual(get_meal, 0)
		
	def test_reverse_success_links(self):
		form_data = self.update_add_food_form("food", "carrot")
		response = self.client.post("/polls/add_food_to_database/", form_data, follow=True)
		self.assertContains(response, "<a href='%s'>Go to Home Page</a>" % reverse("polls:index"), html=True)
		self.assertContains(response, "<a href='%s'>Go to Main Food Page</a>" % reverse("polls:food"), html=True)
		
class GetRememberedMealsTest(TestCase):

	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		self.factory = RequestFactory()
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')
		create_food_database_objects()
		banana = FoodDatabase.objects.get(food="Banana")
		fiber_bar = FoodDatabase.objects.get(food='Fiber One Bar')
		strawberry = FoodDatabase.objects.get(food='Strawberry - Medium')
		orange = FoodDatabase.objects.get(food="Orange")
		half_and_half = FoodDatabase.objects.get(food='Half and Half')
		honey = FoodDatabase.objects.get(food="Honey")
		RememberMeals.objects.create(title="Fruit", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=banana, portion=1, units_consumed=1,
									 units="banana", cal_eaten=110, carbs=27, fat=.4, protein=1.3, sodium=1,
									 sugar=14)
		RememberMeals.objects.create(title="Fruit", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=strawberry, portion=1, units_consumed=9,
									 units="ounces", cal_eaten=4, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
		RememberMeals.objects.create(title="Fruit 2", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=orange, portion=1, units_consumed=7.3,
									 units="oz", cal_eaten=69, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
		RememberMeals.objects.create(title="Fruit 2", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=honey, portion=1, units_consumed=2,
									 units="Teaspoons", cal_eaten=42, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
		RememberMeals.objects.create(title="Fiber", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=fiber_bar, portion=1, units_consumed=40,
									 units="grams", cal_eaten=140, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
		RememberMeals.objects.create(title="Fiber", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=half_and_half, portion=2, units_consumed=2,
									 units="TBSP", cal_eaten=40, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
									 
	def test_remove_duplicates(self):
		get_meal = RememberMeals.objects.filter(user=self.user)
		get_meal_2 = []
		get_meal_2 = remove_duplicates_remember(get_meal, get_meal_2)
		
		#based on setup, should be three separate meal titles
		self.assertEqual(len(get_meal_2), 3)
		first = get_meal_2[0]
		second = get_meal_2[1]
		third = get_meal_2[2]
		self.assertEqual(first.title, "Fruit")
		self.assertEqual(second.title, "Fruit 2")
		self.assertEqual(third.title, "Fiber")
		
	def test_get_my_meals_template(self):
		response = self.client.get("/polls//my_meals/")
		self.assertTemplateUsed("polls/my_meals.html")
		self.assertContains(response, "Your Personal Meals")
		
	def test_response_details(self):
		response = self.client.get("/polls//my_meals/")
		#print(response.content)
		self.assertContains(response, "Search")
		self.assertContains(response, "Fruit")
		self.assertContains(response, "Fruit 2")
		self.assertContains(response, "Fiber")
		self.assertNotContains(response, "Banana")
		self.assertNotContains(response, "Half")
		
	def test_various_search_criteria(self):
		# Fruit should return 2 results
		form_data = {'title_to_search': 'Fruit'}
		response = self.client.post("/polls//my_meals/", form_data)
		self.assertContains(response, "Fruit")
		self.assertContains(response, "Fruit 2")
		self.assertNotContains(response, "Fiber")
		self.assertNotContains(response, "Honey")
		
		#Fruit 2 is one result
		form_data = {'title_to_search': 'Fruit 2'}
		response = self.client.post("/polls//my_meals/", form_data)
		self.assertContains(response, "Fruit 2")
		self.assertNotContains(response, "Fiber")
		
		#blank search returns all titles
		form_data = {'title_to_search': ''}
		response = self.client.post("/polls//my_meals/", form_data)
		self.assertContains(response, "Fruit 2")
		self.assertContains(response, "Fiber")
		
		# search that doesn't match titles returns nothing
		form_data = {'title_to_search': 'Banana'}
		response = self.client.post("/polls//my_meals/", form_data)
		self.assertNotContains(response, "Fruit")
		self.assertNotContains(response, "Fiber")
		
	def test_specific_meal_fruit(self):
		response = self.client.get("/polls/Fruit/my_meals/")
		
		#get title
		self.assertContains(response, 'Meal details for "Fruit"')
		
		self.assertNotContains(response, "Fiber One Bar")
		self.assertNotContains(response, "Half")
		self.assertNotContains(response, "Honey")
		self.assertContains(response, "Banana")
		self.assertContains(response, "1.0 banana")
		self.assertContains(response, "Strawberry - Medium")
		self.assertContains(response, "9.0 ounces")
		
		# calories
		self.assertContains(response, "4.0")
		self.assertContains(response, "110.0")
		
		#carbs
		self.assertContains(response, "27.0")
		
		#total calories
		self.assertContains(response, "114.0")
		
	def test_specific_meal_fruit_2(self):
		response = self.client.get("/polls/Fruit 2/my_meals/")
		
		# get title
		self.assertContains(response, 'Meal details for "Fruit 2"')
		
		# assert contains correct food items
		self.assertContains(response, "Honey")
		self.assertContains(response, "Orange")
		
		# assert not contains food for different meals
		self.assertNotContains(response, "Half and Half")
		self.assertNotContains(response, "Banana")
		self.assertNotContains(response, "Strawberry")
		
		# assert contains correct servings
		self.assertContains(response, "2.0 Teaspoons")
		self.assertContains(response, "7.3 oz")
		
		# assert contains correct calorie amounts
		self.assertContains(response, "42.0")
		self.assertContains(response, "69.0")
		
		#properly adds calories
		self.assertContains(response, "111.0")
		
	def test_reverse_links_meals_template(self):
		response = self.client.get("/polls/Fruit 2/my_meals/")
		
		# clicked a meal
		self.assertContains(response, "<a href='%s'>Fruit 2</a>" 
		                     % reverse("polls:my_meals", kwargs={'title': 'Fruit 2'}), html=True)
		self.assertContains(response, "<a href='%s'>food diary</a>" % reverse("polls:food"), html=True )
		
	def test_delete_meal(self):
		get_meals = RememberMeals.objects.filter(user=self.user).count()
		self.assertEqual(get_meals, 6)
		response = self.client.get("/polls/Fruit 2/my_meals_delete", follow=True)
		get_meals = RememberMeals.objects.filter(user=self.user).count()
		self.assertEqual(get_meals, 4)
		deleted_meal = RememberMeals.objects.filter(user=self.user, title="Fruit 2")
		self.assertFalse(deleted_meal)
		self.assertNotContains(response, "Fruit 2")
		self.assertContains(response, "Fruit")
		self.assertContains(response, "Fiber")
		
class AddFoodTest(TestCase):

	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 1), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		UserDays.objects.create(user=user, date=datetime.date(2017, 5, 30), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 6, 18), done=False)
		create_food_database_objects()
		selected = FoodDatabase.objects.get(food="Banana")
		create_database_record(selected, 1, "banana", "B", 3, "2017-05-30", user, 3)
		create_database_record(selected, 1, "banana", "B", 3, "2017-05-31", user, 3)
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(selected, 1, "ounce", "S", 1.4175, "2017-05-29", user, 2)
		create_database_record(selected, 1, "gram", "D", .5, "2017-06-05", user, 20)
		selected = FoodDatabase.objects.get(food='Half and Half')
		create_database_record(selected, 1, "TBSP", "B", 2, "2017-05-31", user, 2)
		create_database_record(selected, 1, "TBSP", "D", 2, "2017-06-05", user, 2)
		fiber_bar = FoodDatabase.objects.get(food='Fiber One Bar')
		RememberMeals.objects.create(title="ThisMeal", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=fiber_bar, portion=1, units_consumed=40,
									 units="gram", cal_eaten=140, carbs=29, fat=4, protein=2, sodium=90,
									 sugar=10)
		honey = FoodDatabase.objects.get(food="Honey")
		RememberMeals.objects.create(title="ThisMeal", user=self.user, date=datetime.date(2017, 5, 29), 
		                             meal_type="B", food_item=honey, portion=1, units_consumed=2,
									 units="Teaspoons", cal_eaten=42, carbs=0, fat=0, protein=0, sodium=0,
									 sugar=0)
		
	def create_food_items(self):
		global strawberry, brownie, orange
		strawberry = FoodDatabase.objects.get(food="Strawberry - Medium")
		create_database_record(strawberry, 9, "ounces", "B", 1, "2017-06-14", user, 1)
		create_database_record(strawberry, 9, "ounces", "B", 2, "2017-05-30", user, 2)
		brownie = FoodDatabase.objects.get(food="Fiber Brownie")
		create_database_record(brownie, 22, "GMs", "B", 1, "2017-06-14", user, 1)
		create_database_record(brownie, 22, "GMs", "B", 2, "2017-05-31", user, 2)
		orange = FoodDatabase.objects.get(food="Orange")
		create_database_record(orange, 7.3, "oz", "B", 1, "2017-06-15", user, 1)
		
		
		
	def list_food_items(self, query):
		food_items = []
		for q in query:
			food_items.append(q.food_item.food)
		return food_items
		
	def test_query_recent_meals(self):
		user = self.user
		recent_query = query_recent_meals(user)
		food_items = self.list_food_items(recent_query)
		self.assertEqual(len(food_items), 3)
		self.assertTrue('Banana' in food_items)
		self.assertTrue('Fiber One Bar' in food_items)
		self.assertTrue('Half and Half' in food_items)
		
	def test_query_recent_meals_no_quick_add(self):
		# test that quick add is properly excluded from recent query_recent_meals
		
		#first create a quick add record, since its not in set up
		selected = FoodDatabase.objects.get(food="Quick Add")
		create_database_record(selected, 1, "calorie", "B", 100, "2017-05-30", user, 100)
		
		# test that I properly created the quick add record
		get_quick_add = UserMeals.objects.filter(food_item=selected).count()
		self.assertEqual(get_quick_add, 1)
		
		# tomorrow-finish making test, run recent query, test items, assert no Quick Add
		get_query = query_recent_meals(user)
		self.assertEqual(3, len(get_query))
		food_items = self.list_food_items(get_query)
		self.assertTrue('Fiber One Bar' in food_items)
		self.assertTrue('Quick Add' not in food_items)
		
	def test_six_food_items(self):
		# test that with 6 food items, the five most recent are picked
		
		#since we only have three unique food items, need to create 3 more
		self.create_food_items()
		
		# run query_recent_meals
		get_query = query_recent_meals(user)
		
		#list should only have first 5 items
		self.assertEqual(5, len(get_query))
		
		#convert to a list where you can assert the name of the food item
		# is in the list as opposed to the database object
		food_items = self.list_food_items(get_query)
		
		#the first five unique items when sorted by date should be in list
		self.assertTrue("Strawberry - Medium" in food_items)
		self.assertTrue("Fiber Brownie" in food_items)
		self.assertTrue("Orange" in food_items)
		self.assertTrue("Half and Half" in food_items)
		self.assertTrue("Fiber One Bar" in food_items)
		
		# the 2 bananas are 5-30 and 5-31, after 6/5 and 6/14 for other food items
		# thus, banana shouldn't be in recent query
		self.assertTrue("Banana" not in food_items)
		
	def test_frequent_query_6_items_get_most_frequent(self):
		# test that with 6 food items, 5 most frequent are picked
		# 5 food items have 2 meals, 1 has 1 meal
		# banana, fiber one bar, half and half have 2 meals from set up. 
		# latest date is 6/5/17
		
		#run create_food_items to create meals for orange, strawberry, 
		# and fiber brownie
		
		# 2 brownie meals, 2 strawberry meals, 1 orange meal
		# latest date for strawberry and brownie meals are 6/14
		# latest date for orange is 6/15
		
		self.create_food_items()
		
		# run frequent query function
		get_query = query_frequent_meals(user)
		
		# test that there are 5 items in list, because
		# function cuts off at 5 list items
		self.assertEqual(5, len(get_query))
		
		# convert list to names of food items for testing
		food_items = self.list_food_items(get_query)
		
		# orange should not be in food items since there's 
		#only one meal for it
		self.assertTrue("Orange" not in food_items)
		
		###
		#strawberry, banana, fiber bar, brownie, and half and half
		#should be in food_items since they each have 2 meals
		
		self.assertTrue("Banana" in food_items)
		self.assertTrue("Strawberry - Medium" in food_items)
		self.assertTrue("Half and Half" in food_items)
		self.assertTrue("Fiber Brownie" in food_items)
		self.assertTrue("Fiber One Bar" in food_items)
		
		# test that the most recent banana record pulled
		banana = FoodDatabase.objects.get(food="Banana")
		get_banana = UserMeals.objects.get(user=self.user, date=datetime.date(2017, 5, 31), 
		                                      food_item=banana)
		self.assertTrue(get_banana in get_query)
		
		# test most recent fiber one bar pulled
		fiber_bar = FoodDatabase.objects.get(food="Fiber One Bar")
		get_fiber_bar = UserMeals.objects.get(user=self.user, date=datetime.date(2017, 6, 5),
		                                      food_item=fiber_bar)
		self.assertTrue(get_fiber_bar in get_query)
		
		# test most recent strawberry pulled
		strawberry = FoodDatabase.objects.get(food="Strawberry - Medium")
		get_strawberry = UserMeals.objects.get(user=self.user, date=datetime.date(2017, 6, 14),
		                                      food_item=strawberry)
		self.assertTrue(get_strawberry in get_query)
		
		# test most recent fiber brownie pulled
		fiber_brownie = FoodDatabase.objects.get(food="Fiber Brownie")
		get_brownie = UserMeals.objects.get(user=self.user, date=datetime.date(2017, 6, 14),
		                                      food_item=fiber_brownie)
		self.assertTrue(get_brownie in get_query)
		
		# test most recent half and half pulled
		half_and_half = FoodDatabase.objects.get(food="Half and Half")
		get_half_and_half = UserMeals.objects.get(user=self.user, date=datetime.date(2017, 6, 5),
		                                      food_item=half_and_half)
		self.assertTrue(get_half_and_half in get_query)
		
	def test_frequent_query_quick_add(self):
		# create 3 versions of quick add, ensure its not in 
		# frequent query
		
		selected = FoodDatabase.objects.get(food="Quick Add")
		create_database_record(selected, 1, "calorie", "B", 100, "2017-06-17", user, 100)
		create_database_record(selected, 1, "calorie", "B", 100, "2017-06-15", user, 100)
		create_database_record(selected, 1, "calorie", "B", 100, "2017-05-30", user, 100)
		
		# validate that I created 3 quick add meals
		get_quick = UserMeals.objects.filter(user=self.user, food_item=selected).count()
		self.assertEqual(get_quick, 3)
		
		# create 2 strawberry, 2 brownie, 1 orange
		self.create_food_items()
		
		# run frequent query
		get_query = query_frequent_meals(user)
		self.assertEqual(len(get_query), 5)
		
		# get list of food item names as opposed to database objects
		food_items = self.list_food_items(get_query)
		
		# quick add should not be in food_items
		self.assertTrue("Quick Add" not in food_items)
		
		# check a couple things that should be in food items, 
		# to validate test is working properly
		self.assertTrue("Banana" in food_items)
		self.assertTrue("Strawberry - Medium" in food_items)
		self.assertEqual(len(food_items), 5)
		
	def test_frequent_query_3_items(self):
		
		# test again that quick add excluded
		# test that if less than 5 items, get list with all unique food items
		# set up has 3 unique food items, will create quick add but nothing else
		
		# create Quick Adds
		selected = FoodDatabase.objects.get(food="Quick Add")
		create_database_record(selected, 1, "calorie", "B", 100, "2017-06-17", user, 100)
		create_database_record(selected, 1, "calorie", "B", 100, "2017-06-15", user, 100)
		create_database_record(selected, 1, "calorie", "B", 100, "2017-05-30", user, 100)
		
		# validate that I created 3 quick add meals
		get_quick = UserMeals.objects.filter(user=self.user, food_item=selected).count()
		self.assertEqual(get_quick, 3)
		
		get_query = query_frequent_meals(user)
		self.assertEqual(len(get_query), 3)
		
		# get food names from query
		food_items = self.list_food_items(get_query)
		
		self.assertTrue("Quick Add" not in food_items)
		self.assertEqual(len(food_items), 3)
		self.assertTrue("Fiber One Bar" in food_items)
		self.assertTrue("Banana" in food_items)
		self.assertTrue("Half and Half" in food_items)
		
	def test_add_food_choices(self):
		# result should be tuples of tuples, test various combos
		
		# first need to get list of UserMeals database objects
		brownie = FoodDatabase.objects.get(food="Fiber Brownie")
		create_database_record(brownie, 22, "gm", "B", 1, "2017-06-06", user, 1)
		fiber_bar = FoodDatabase.objects.get(food="Fiber One Bar")
		create_database_record(fiber_bar, 40, "gram", "B", 1, "2017-06-07", user, 1)
		half = FoodDatabase.objects.get(food="Half and Half")
		create_database_record(half, 2, "tbsp", "B", 1, "2017-06-08", user, 1)
		strawberry = FoodDatabase.objects.get(food="Strawberry - Medium")
		create_database_record(strawberry, 1, "ounce", "B", 1, "2017-06-09", user, 1)
		one_milk = FoodDatabase.objects.get(food="1% Milk")
		create_database_record(one_milk, 2, "cup", "B", 1, "2017-06-10", user, 1)
		
		get_query = query_recent_meals(user)
		add_food_choices = create_add_food_choices(get_query, user)
		one_milk = add_food_choices[0]
		expected = (('2.0 cups', '2.0 cups'), ('1 cup', '1 cup'), ('1 tbsp', '1 tbsp'),
		             ('1 tsp', '1 tsp'), ('1 fluid ounce', '1 fluid ounce'))
		strawberry = add_food_choices[1]
		expected = (('1.0 ounce', '1.0 ounce'), ('1 gram', '1 gram'))
		self.assertEqual(strawberry, expected)
		half = add_food_choices[2]
		expected = (('2.0 tbsps', '2.0 tbsps'), ('1 cup', '1 cup'), ('1 tbsp', '1 tbsp'), 
		            ('1 tsp', '1 tsp'), ('1 fluid ounce', '1 fluid ounce'))
		self.assertEqual(half, expected)
		fiber_bar = add_food_choices[3]
		expected = (('40.0 grams', '40.0 grams'), ('1 gram', '1 gram'), ('1 ounce', '1 oz'))
		self.assertEqual(fiber_bar, expected)
		brownie = add_food_choices[4]
		expected = (('22.0 gms', '22.0 gms'), ('1 gram', '1 gram'), ('1 ounce', '1 oz'))
		self.assertEqual(brownie, expected)
		
	def test_add_food_choices_more_units(self):
		# test choices you get for servings and units of:
		# 1 gram, 1 gm, 1 oz, 1 tbsp, plural teaspoon
		
		# create database records with servings and units we
		# need for test
		
		brownie = FoodDatabase.objects.get(food="Fiber Brownie")
		create_database_record(brownie, 1, "gm", "B", 1, "2017-06-06", user, 1)
		fiber_bar = FoodDatabase.objects.get(food="Fiber One Bar")
		create_database_record(fiber_bar, 1, "gram", "B", 1, "2017-06-07", user, 1)
		half = FoodDatabase.objects.get(food="Half and Half")
		create_database_record(half, 1, "tbsp", "B", 1, "2017-06-08", user, 1)
		strawberry = FoodDatabase.objects.get(food="Strawberry - Medium")
		create_database_record(strawberry, 3, "ounce", "B", 1, "2017-06-09", user, 1)
		orange = FoodDatabase.objects.get(food="Orange")
		create_database_record(orange, 1, "oz", "B", 1, "2017-06-10", user, 1)
		
		get_query = query_recent_meals(user)
		add_food_choices = create_add_food_choices(get_query, user)
		
		orange = add_food_choices[0]
		expected = (('1.0 oz', '1.0 oz'), ('1 gram', '1 gram'))
		self.assertEqual(orange, expected)
		strawberry = add_food_choices[1]
		expected = (('3.0 ounces', '3.0 ounces'), ('1 gram', '1 gram'), ('1 ounce', '1 oz'))
		self.assertEqual(strawberry, expected)
		half = add_food_choices[2]
		expected = (('1.0 tbsp', '1.0 tbsp'), ('1 cup', '1 cup'), 
		            ('1 tsp', '1 tsp'), ('1 fluid ounce', '1 fluid ounce'))
		self.assertEqual(half, expected)
		fiber_bar = add_food_choices[3]
		expected = (('1.0 gram', '1.0 gram'), ('1 ounce', '1 oz'))
		self.assertEqual(fiber_bar, expected)
		brownie = add_food_choices[4]
		expected = (('1.0 gm', '1.0 gm'), ('1 ounce', '1 oz'))
		self.assertEqual(brownie, expected)
		
		two_milk = FoodDatabase.objects.get(food="2% Milk")
		create_database_record(two_milk, 1, "fl oz", "B", 1, "2017-06-11", user, 1)
		honey = FoodDatabase.objects.get(food="Honey")
		create_database_record(honey, 2, "teaspoon", "B", 1, "2017-06-12", user, 1)
		
		get_query = query_recent_meals(user)
		add_food_choices = create_add_food_choices(get_query, user)
		
		honey = add_food_choices[0]
		expected = (('2.0 teaspoons', '2.0 teaspoons'), ('1 cup', '1 cup'), ('1 tbsp', '1 tbsp'),
		             ('1 tsp', '1 tsp'), ('1 fluid ounce', '1 fluid ounce'))
		self.assertEqual(honey, expected)
		two_milk = add_food_choices[1]
		expected = (('1.0 fl oz', '1.0 fl oz'), ('1 cup', '1 cup'), ('1 tbsp', '1 tbsp'),
		             ('1 tsp', '1 tsp'))
		self.assertEqual(two_milk, expected)
		remembered = add_food_choices[5]
		expected = (('1 Meal', '1 Meal'),)
		self.assertEqual(remembered, expected)
		
	def test_add_names(self):
		get_query = query_recent_meals(user)
		get_food_names = food_names(get_query)
		expected = ['Fiber One Bar', 'Half and Half', 'Banana']
		self.assertEqual(get_food_names, expected)
		
	def test_template_used(self):
		response = self.client.get("/polls/2017-05-30/Breakfast/add_food/")
		self.assertTemplateUsed("polls/add_food.html")
		
	def test_template_form_initials(self):
		response = self.client.get("/polls/2017-05-30/Breakfast/add_food/")
		
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Banana")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "ThisMeal")
		self.assertContains(response, "3.0")
		self.assertContains(response, ".5")
		self.assertContains(response, "2.0")
		self.assertContains(response, "1.0")
		
		# servings banana
		self.assertContains(response, "1.0 banana")
		# servings fiber bar
		self.assertContains(response, "40.0 grams")
		self.assertContains(response, "1 gram")
		self.assertContains(response, "1 ounce")
		
		#servings half and half
		self.assertContains(response, "1.0 TBSP")
		self.assertContains(response, "1 cup")
		self.assertContains(response, "1 tsp")
		self.assertContains(response, "1 fluid ounce")
		
		# servings remembered meal
		self.assertContains(response, "1 Meal")
		
		# test hidden fields
		self.assertContains(response,
		                   '<input id="id_form-6-today" name="form-6-today" type="hidden" value="2017-05-30" />')
		self.assertContains(response, 
						   '<input id="id_form-6-meal" name="form-6-meal" type="hidden" value="Breakfast" />')
		self.assertContains(response,
							'<input id="id_form-0-formset_index" name="form-0-formset_index" type="hidden" value="0" />')
							
	def test_template_recents_and_frequents(self):
		
		# create distinct meals that will be on frequent tab
		# vs recent tab
		
		# set up has 2 banana, 2 fiber bar, 2 half and half
		# create two honey and orange
		honey = FoodDatabase.objects.get(food="Honey")
		create_database_record(honey, 2, "teaspoon", "B", 1, "2017-05-30", user, 1)
		create_database_record(honey, 2, "teaspoon", "B", 1, "2017-05-29", user, 1)
		
		orange = FoodDatabase.objects.get(food="Orange")
		create_database_record(orange, 7.3, "oz", "B", 1, "2017-05-30", user, 1)
		create_database_record(orange, 7.3, "oz", "B", 1, "2017-05-29", user, 1)
		
		# create recent meals, unique food items
		strawberry = FoodDatabase.objects.get(food="Strawberry - Medium")
		create_database_record(strawberry, 9, "oz", "B", 1, "2017-06-16", user, 1)
		brownie = FoodDatabase.objects.get(food="Fiber Brownie")
		create_database_record(brownie, 22, "GMs", "B", 1, "2017-06-16", user, 1)
		one_milk = FoodDatabase.objects.get(food="1% Milk")
		create_database_record(one_milk, 2, "cups", "B", 1, "2017-06-16", user, 1)
		two_milk = FoodDatabase.objects.get(food="2% Milk")
		create_database_record(two_milk, 1, "fl oz", "B", 1, "2017-06-16", user, 1)
		peanut_butter = FoodDatabase.objects.get(food="Peanut Butter")
		create_database_record(peanut_butter, 2, "Tablespoons", "B", 1, "2017-06-16", user, 1)
		
		# user clicks "Add Food"
		response = self.client.get("/polls/2017-05-30/Breakfast/add_food/")
		
		# assert all the food names are in response
		
		#frequents
		self.assertContains(response, "Banana")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "Honey")
		self.assertContains(response, "Orange")
		
		#recents
		self.assertContains(response, "Strawberry - Medium")
		self.assertContains(response, "Fiber Brownie")
		self.assertContains(response, "1% Milk")
		self.assertContains(response, "2% Milk")
		self.assertContains(response, "Peanut Butter")
		
		# test that there are 11 forms
		self.assertContains(response,
							'<input id="id_form-10-formset_index" name="form-10-formset_index" type="hidden" value="10" />')
		
		
		# test that recent and frequent are on correct tabs based on serve size
		
		# strawberry should be first form, most recent
		straw_text = '<select id="id_form-0-serve_size" name="form-0-serve_size">\n<option value="9.0 ozs">'
		self.assertContains(response, straw_text)
		
		# banana should be frequent, form id 5-9
		banana_text = '<select id="id_form-5-serve_size" name="form-5-serve_size">\n<option value="1.0 banana">'
		self.assertContains(response, banana_text)
		
		# ThisMeal should be meals, form id 10
		this_meal_text = '<select id="id_form-10-serve_size" name="form-10-serve_size">\n<option value="1 Meal">'
		self.assertContains(response, this_meal_text)
		
	def test_initial_values_form(self):
		response = self.client.get("/polls/2017-05-30/Breakfast/add_food/")
		self.assertEqual(response.context['meal_formset'].initial[0].get('food_quant'), .5)
		self.assertEqual(response.context['meal_formset'].initial[1].get('food_quant'), 2)
		self.assertEqual(response.context['meal_formset'].initial[2].get('food_quant'), 3)
		self.assertEqual(response.context['meal_formset'].initial[6].get('food_quant'), 1)
		expected = (('40.0 grams', '40.0 grams'), ('1 gram', '1 gram'), ('1 ounce', '1 oz'))
		self.assertEqual(response.context['meal_formset'].form_kwargs['add_food'][0], expected)
		expected = (('1.0 TBSP', '1.0 TBSP'), ('1 cup', '1 cup'), ('1 tsp', '1 tsp'),
		            ('1 fluid ounce', '1 fluid ounce'))
		self.assertEqual(response.context['meal_formset'].form_kwargs['add_food'][1], expected)
		expected = (('1.0 banana', '1.0 banana'),)
		self.assertEqual(response.context['meal_formset'].form_kwargs['add_food'][2], expected)
		expected = (('1 Meal', '1 Meal'),)
		self.assertEqual(response.context['meal_formset'].form_kwargs['add_food'][6], expected)
		self.assertEqual(response.context['meal_formset'].form_kwargs['today'], 
		                 '2017-05-30')
		self.assertEqual(response.context['meal_formset'].form_kwargs['meal'],
                 		'Breakfast')
						
						
	def post_data_one_form(self, selected, food_quant, formset_index, serve_size):
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 1,
				'form-INITIAL_FORMS': 1,
				'form-0-food_selected': selected,
				'form-0-food_quant': food_quant,
				'form-0-formset_index': formset_index,
				'form-0-serve_size': serve_size,
				'form-0-today': "2017-05-30",
				'form-0-meal': "Breakfast",}
		return post_data
		
	def test_post_valid_data(self):
		post_data = self.post_data_one_form(True, 20, 0, "1 gram")
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
		
		# indicates no form errors, renders "polls/food.html"
		self.assertContains(response, "Calories")
	
		
	def test_fiber_invalid_quantity(self):
		post_data = self.post_data_one_form(True, -5, 0, "1 gram")
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=0,
            field='food_quant',
            errors='Ensure this value is greater than or equal to 0.1.',
        )
		
		
		# if form fails, it doesn't render polls/food.html
		# thus, the word "Calories" will not be in response
		self.assertNotContains(response, "Calories")
		
	def test_fiber_still_invalid_quantity(self):
		post_data = self.post_data_one_form(True, 0, 0, "1 gram")
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=0,
            field='food_quant',
            errors='Ensure this value is greater than or equal to 0.1.',
        )
		
		
		# if form fails, it doesn't render polls/food.html
		# thus, the word "Calories" will not be in response
		self.assertNotContains(response, "Calories")
		
	def test_fiber_blank_quantity(self):
		post_data = self.post_data_one_form(True, "", 0, "1 gram")
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=0,
            field='food_quant',
            errors='This field is required.',
        )
		
		
		# if form fails, it doesn't render polls/food.html
		# thus, the word "Calories" will not be in response
		self.assertNotContains(response, "Calories")
		
	def test_fiber_invalid_serve_size(self):
		post_data = self.post_data_one_form(True, 10, 0, "20.0 gram")
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=0,
            field='serve_size',
            errors='Select a valid choice. 20.0 gram is not one of the available choices.',
        )
		
		
		# if form fails, it doesn't render polls/food.html
		# thus, the word "Calories" will not be in response
		self.assertNotContains(response, "Calories")
		
	def test_multiple_forms_invalid_data(self):
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 2,
				'form-INITIAL_FORMS': 2,
				'form-0-food_selected': True,
				'form-0-food_quant': 1,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-05-30",
				'form-0-meal': "Breakfast",
				'form-1-food_selected': True,
				'form-1-food_quant': "rabbit",
				'form-1-formset_index': 1,
				'form-1-serve_size': "40.0 grams",
				'form-1-today': "",
				'form-1-meal': "",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-05-30', 'name': 'Breakfast'}), post_data, follow=True)
									
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=1,
            field='food_quant',
            errors='Enter a number.',
        )
		
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=1,
            field='serve_size',
            errors='Select a valid choice. 40.0 grams is not one of the available choices.',
        )
		
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=1,
            field='meal',
            errors='This field is required.',
        )
		
		self.assertFormsetError(
            response,
            formset='meal_formset',
            form_index=1,
            field='today',
            errors='This field is required.',
        )
		
		
		# if form fails, it doesn't render polls/food.html
		# thus, the word "Calories" will not be in response
		self.assertNotContains(response, "Calories")
		
	# test template and user meal results after posting data
	
	def test_no_food_checked(self):
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 2,
				'form-INITIAL_FORMS': 2,
				'form-0-food_selected': False,
				'form-0-food_quant': 1,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-06-18",
				'form-0-meal': "Lunch",
				'form-1-food_selected': False,
				'form-1-food_quant': 2,
				'form-1-formset_index': 1,
				'form-1-serve_size': "1.0 TBSP",
				'form-1-today': "2017-06-18",
				'form-1-meal': "Lunch",
				'form-2-food_selected': False,
				'form-2-food_quant': 2,
				'form-2-formset_index': 1,
				'form-2-serve_size': "1.0 banana",
				'form-2-today': "2017-06-18",
				'form-2-meal': "Lunch",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-06-18', 'name': 'Lunch'}), post_data, follow=True)
									
		# prove that it went to polls/food.html
		self.assertContains(response, "Calories")
		self.assertContains(response, "Quick Tools")
		
		# didnt add any food to the page
		self.assertNotContains(response, "Half and Half")
		self.assertNotContains(response, "Fiber")
		self.assertNotContains(response, "Banana")
		
	def test_5_bananas(self):
		# check bananas, mark 5 as eaten, 
		# test that properly shows 5.0 banans
		# shows 550 calories, shows correct amount of carbs
		# still shouldn't show fiber or half and half
		
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 3,
				'form-INITIAL_FORMS': 3,
				'form-0-food_selected': False,
				'form-0-food_quant': 1,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-06-18",
				'form-0-meal': "Lunch",
				'form-1-food_selected': False,
				'form-1-food_quant': 2,
				'form-1-formset_index': 1,
				'form-1-serve_size': "1.0 TBSP",
				'form-1-today': "2017-06-18",
				'form-1-meal': "Lunch",
				'form-2-food_selected': True,
				'form-2-food_quant': 5,
				'form-2-formset_index': 2,
				'form-2-serve_size': "1.0 banana",
				'form-2-today': "2017-06-18",
				'form-2-meal': "Lunch",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-06-18', 'name': 'Lunch'}), post_data, follow=True)
		
		
		# prove that it went to polls/food.html
		self.assertContains(response, "Calories")
		self.assertContains(response, "Quick Tools")
		self.assertContains(response, "Banana")
		self.assertContains(response, "5.0 bananas")
		# 5 * 110 calories per banana
		self.assertContains(response, "550.0")
		# 5 * 27 carbs per banana
		self.assertContains(response, "135.0")
		
		# didnt add any food to the page
		self.assertNotContains(response, "Half and Half")
		self.assertNotContains(response, "Fiber")
		
	def test_banana_and_fiber(self):
		# check banana and fiber
		# make sure template shows both
		# check that UserMeals was created for both
		
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 3,
				'form-INITIAL_FORMS': 3,
				'form-0-food_selected': True,
				'form-0-food_quant': .5,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-06-18",
				'form-0-meal': "Lunch",
				'form-1-food_selected': False,
				'form-1-food_quant': 2,
				'form-1-formset_index': 1,
				'form-1-serve_size': "1.0 TBSP",
				'form-1-today': "2017-06-18",
				'form-1-meal': "Lunch",
				'form-2-food_selected': True,
				'form-2-food_quant': 5,
				'form-2-formset_index': 2,
				'form-2-serve_size': "1.0 banana",
				'form-2-today': "2017-06-18",
				'form-2-meal': "Lunch",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-06-18', 'name': 'Lunch'}), post_data, follow=True)
		
		
		# prove that it went to polls/food.html
		self.assertContains(response, "Calories")
		self.assertContains(response, "Quick Tools")
		self.assertContains(response, "Banana")
		self.assertContains(response, "5.0 bananas")
		# 5 * 110 calories per banana
		self.assertContains(response, "550.0")
		# 5 * 27 carbs per banana
		self.assertContains(response, "135.0")
		
		# test fiber
		self.assertContains(response, "Fiber One Bar")
		# half of 140 calories, half a serving size
		self.assertContains(response, "70.0")
		# should show half of 1 serving of carbs
		self.assertContains(response, "14.5")
		
		# didnt add any food to the page
		self.assertNotContains(response, "Half and Half")
		
		# assert banana UserMeals created 6/18/17
		banana = FoodDatabase.objects.get(food="Banana")
		get_query = UserMeals.objects.filter(user=user, date=datetime.date(2017, 6, 18), 
		                                      food_item=banana).count()
		self.assertEqual(get_query, 1)
		fiber_bar = FoodDatabase.objects.get(food="Fiber One Bar")
		get_fiber = UserMeals.objects.filter(user=user, date=datetime.date(2017, 6, 18),
		                                     food_item=fiber_bar).count()
		self.assertEqual(get_fiber, 1)
		
	def test_template_half_and_half(self):
		# change units on half and half, make sure
		# calories is correct
		
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 3,
				'form-INITIAL_FORMS': 3,
				'form-0-food_selected': False,
				'form-0-food_quant': .5,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-06-18",
				'form-0-meal': "Lunch",
				'form-1-food_selected': True,
				'form-1-food_quant': 2,
				'form-1-formset_index': 1,
				'form-1-serve_size': "1 tsp",
				'form-1-today': "2017-06-18",
				'form-1-meal': "Lunch",
				'form-2-food_selected': False,
				'form-2-food_quant': 5,
				'form-2-formset_index': 2,
				'form-2-serve_size': "1.0 banana",
				'form-2-today': "2017-06-18",
				'form-2-meal': "Lunch",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-06-18', 'name': 'Lunch'}), post_data, follow=True)
		
		self.assertContains(response, "Calories")
		self.assertContains(response, "Half and Half")
		
		# correct units
		self.assertContains(response, "2.0 tsps")
		# correct calorie count
		self.assertContains(response, "13.3")
		
	def test_remembered_meal(self):
	
		# simulate user selecting remembered meal
		# remembered meal is "ThisMeal", which has 40 grams
		# fiber bar, and 2 teaspoons of honey
		post_data={
				'username': None,
				'form-TOTAL_FORMS': 7,
				'form-INITIAL_FORMS': 7,
				'form-0-food_selected': False,
				'form-0-food_quant': 3,
				'form-0-formset_index': 0,
				'form-0-serve_size': "40.0 grams",
				'form-0-today': "2017-06-18",
				'form-0-meal': "Lunch",
				'form-1-food_selected': False,
				'form-1-food_quant': 3,
				'form-1-formset_index': 1,
				'form-1-serve_size': "1.0 TBSP",
				'form-1-today': "2017-06-18",
				'form-1-meal': "Lunch",
				'form-2-food_selected': False,
				'form-2-food_quant': 3,
				'form-2-formset_index': 2,
				'form-2-serve_size': "1.0 banana",
				'form-2-today': "2017-06-18",
				'form-2-meal': "Lunch",
				'form-3-food_selected': True,
				'form-3-food_quant': 2,
				'form-3-formset_index': 3,
				'form-3-serve_size': "1.0 banana",
				'form-3-today': "2017-06-18",
				'form-3-meal': "Lunch",
				'form-4-food_selected': False,
				'form-4-food_quant': 3,
				'form-4-formset_index': 4,
				'form-4-serve_size': "40.0 grams",
				'form-4-today': "2017-06-18",
				'form-4-meal': "Lunch",
				'form-5-food_selected': False,
				'form-5-food_quant': 3,
				'form-5-formset_index': 5,
				'form-5-serve_size': "1.0 TBSP",
				'form-5-today': "2017-06-18",
				'form-5-meal': "Lunch",
				'form-6-food_selected': True,
				'form-6-food_quant': 3,
				'form-6-formset_index': 6,
				'form-6-serve_size': "1 Meal",
				'form-6-today': "2017-06-18",
				'form-6-meal': "Lunch",}
				
		response = self.client.post(reverse('polls:add_food', 
		                            kwargs={'today': '2017-06-18', 'name': 'Lunch'}), post_data, follow=True)
		
		# tempalte contains remembered meals
		self.assertContains(response, "Calories")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Honey")
		
		# calculated calories correctly
		
		# fiber bar=140 calories * 3
		self.assertContains(response, "420.0")
		
		# honey= 42 calories * 3 servings
		self.assertContains(response, "126.0")
		
		# created UserMeals for fiber and honey
		fiber = FoodDatabase.objects.get(food="Fiber One Bar")
		get_fiber = UserMeals.objects.get(food_item=fiber, date=datetime.date(2017, 6, 18),
		                                  user=user)
		self.assertEqual(420, get_fiber.cal_eaten)
		honey = FoodDatabase.objects.get(food="Honey")
		get_honey = UserMeals.objects.get(food_item=honey, date=datetime.date(2017, 6, 18), user=user)
		self.assertEqual(126, get_honey.cal_eaten)
		
		# test the banana
		self.assertContains(response, "Banana")
		self.assertContains(response, "2.0 banana")
		#110 calories * 2
		self.assertContains(response, "220.0")
		# 27 carbs * 2
		self.assertContains(response, "54.0")
		
		banana = FoodDatabase.objects.get(food="Banana")
		get_banana = UserMeals.objects.get(food_item=banana, date=datetime.date(2017, 6, 18), user=user)
		self.assertEqual(220, get_banana.cal_eaten)
		
		
		
	
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
	
		
		
		
		
		