import datetime
from freezegun import freeze_time

from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from django.test import TestCase, RequestFactory
from django.test.client import Client, RequestFactory
from django.test import Client
from django.urls import reverse

from django.db.models import Count

from .models import UserProfileForm, UserProfile, UserDays, RememberMeals, UserMeals
from .views import index, food, signup, user_profile, calculate_net_calories, calculate_BMR, get_nutrient_goals
from .views import *
from .forms import SignUpForm, UserMealsForm, QuickAddForm
from polls import views

class SimpleTest(TestCase):

	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(
			username='jacob', email='jacob@...')
		self.user.set_password('top_secret')
		self.user.save()
		
	
	
	# test homepage for logged in user
	def test_details(self):
		request = self.factory.get('/index/')
		request.user = self.user
		response = index(request)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Hi jacob")
		self.assertContains(response, "Food")
		self.assertContains(response, "My Meals")
		self.assertContains(response, "logout")
		self.assertContains(response, '<a href="%s">Food</a>' % reverse("polls:food"), html=True)
		self.assertContains(response, '<a href="%s">My Meals</a>' % reverse("polls:my_meals", kwargs={'title': "None"}), html=True)
		self.assertNotContains(response, "Login")
		self.assertNotContains(response, "Sign Up")
		
	# should show login and sign up  but not food or mymeals
	def test_homepage_anonymous_user(self):
		request = self.factory.get('/index/')
		request.user = AnonymousUser()
		response = index(request)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '<a href="%s"><h4>Login</h4></a>' % reverse("polls:login"), html=True)
		self.assertContains(response, '<a href="%s"><h4>Sign Up</h4></a>' % reverse("polls:signup"), html=True)
		self.assertNotContains(response, "Food")
		self.assertNotContains(response, "My Meals")
		self.assertNotContains(response, "logout")
		
	def test_sign_up(self):
		form_data = {
			'username': 'jacob1',
			'first_name': 'Jacob',
			'last_name': 'Lopez',
			'password1': 'hello123',
			'password2': 'hello122',
			'email': 'jacob@gmail.com',
		}
		form = SignUpForm(data=form_data)
		if form.is_valid():
			self.fail('Form should not be valid')
		form_data['password2'] = 'hello123'
		form = SignUpForm(data=form_data)
		if not form.is_valid():
			self.fail('Form should be valid')
		form_data['username'] = ''
		form = SignUpForm(data=form_data)
		if form.is_valid():
			self.fail('Form should not be valid-no username')
		
	def test_sign_up_gets_correct_form(self):
		response = self.client.get('/polls/signup/')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'polls/signup.html')
		self.assertIsInstance(response.context['form'], SignUpForm)
	
	def test_sign_up_redirect(self):
		form_data = {
			'username': 'jacob1',
			'first_name': 'Jacob',
			'last_name': 'Lopez',
			'password1': 'hello123',
			'password2': 'hello123',
			'email': 'jacob@gmail.com',
		}
		response = self.client.post('/polls/signup/', form_data)
		self.assertRedirects(response, '/polls/user_profile/')
		get_user = User.objects.get(username='jacob1', email='jacob@gmail.com')
		self.assertIsNotNone(get_user.username)
		self.assertTrue(get_user.is_authenticated)
		try:
			with transaction.atomic():
				new_user = User.objects.create_user(username='jacob1', password='hello123', email='jodie@gmail.com')
		except:
			new_user = 0
		if new_user != 0:
			self.fail("Can't have two users with same username")
		# figure this out-try to log in user with wrong password
		c = Client()
		logged_in = c.login(username='jacob1', password='hello122')
		user = authenticate(username='jacob1', password='hello122')
		self.assertEqual(user, None)
		req = self.factory.get(reverse('polls:login'))
		form = AuthenticationForm(request=req, data={
			'username': 'jacob1', 'password': 'wrong_password'})
		self.assertFalse(form.is_valid())
		
class UpdateFoodDiary(TestCase):

	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(
			username='jacob', email='jacob@...', password='top_secret')

	def test_food_login_required(self):
		request = self.factory.get('polls/food')
		request.user = AnonymousUser()
		response = food(request)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/polls/login/?next=/pollsfood')
		
class SetUp_Class(TestCase):

	def setUp(self):
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')
		
def change_form_data_and_run_form(form_field, form_field_value):
	global profile_form_data
	profile_form_data = {
			'weight': 110,
			'height_ft': 5,
			'height_in': 0,
			'goal_weight': 104,
			'gender': 'F',
			'birth_date': '10/01/1991',
			'zip_code': 10005,
			'lifestyle': 'S',
			'workouts_week': 0,
			'min_per_workout': 30,
			'goal': 'L2',
		}
	profile_form_data[form_field] = form_field_value
	form = UserProfileForm(data=profile_form_data)
	return form.is_valid()
		
class UserProfileTest(TestCase):

	def setUp(self):
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob', password='top_secret')

	
	def test_get_request_user_profile(self):
		response = self.client.get('/polls/user_profile/')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'polls/user_profile.html')
		self.assertIsInstance(response.context['form'], UserProfileForm)
		
	
		
	def test_invalid_min_per_workout(self):
		valid_form = change_form_data_and_run_form('min_per_workout', 30.5)
		self.assertFalse(valid_form)
		
	def test_invalid_data_user_profile_form(self):
		valid_form = change_form_data_and_run_form('weight', 115)
		self.assertTrue(valid_form)
		valid_form = change_form_data_and_run_form('weight', 100.1111111)
		self.assertTrue(valid_form)
		valid_form = change_form_data_and_run_form('weight', 'candy')
		self.assertFalse(valid_form)
		valid_form = change_form_data_and_run_form('weight', -5)
		self.assertFalse(valid_form)
		valid_form = change_form_data_and_run_form('weight', 0)
		self.assertFalse(valid_form)
		valid_form = change_form_data_and_run_form('weight', .1)
		self.assertTrue(valid_form)
		valid_form = change_form_data_and_run_form('weight', None)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('height_ft', 9)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('height_ft', 7)
		self.assertTrue(valid_form)
		
		valid_form = change_form_data_and_run_form('height_ft', 6.5)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('height_in', 13)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('height_in', -5)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('height_in', 12)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('gender', 'S')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('birth_date', '10/1/19912')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('birth_date', '13/1/1991')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('birth_date', '11/111/1991')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('birth_date', '11/1/91')
		self.assertTrue(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '209010')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '2090')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '-2090')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '-20901')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '00001')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('zip_code', '10000')
		self.assertTrue(valid_form)
		
		valid_form = change_form_data_and_run_form('lifestyle', 'B')
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('goal_weight', 0)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('goal_weight', -5)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('goal_weight', .1)
		self.assertTrue(valid_form)
		
		valid_form = change_form_data_and_run_form('min_per_workout', -1)
		self.assertFalse(valid_form)
		
		valid_form = change_form_data_and_run_form('min_per_workout', 0)
		self.assertTrue(valid_form)
		
	def test_post_valid_data(self):
		valid_form = change_form_data_and_run_form('weight', 110)
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'polls/initial_goals.html')
		
	def test_post_invalid_data(self):
		valid_form = change_form_data_and_run_form('weight', None)
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'polls/user_profile.html')
		
	@freeze_time("2017-05-29")
	def test_calculate_bmr(self):
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'S', 'L2', 
		                    0, 0, 0, 0, 0, 0)
		get_BMR = calculate_BMR(profile)
		self.assertEqual(1396, round(get_BMR, 0))
		profile = Profile(110, 5, 0, '10/01/1991', 'M', 'S', 'L2',
		                    0, 0, 0, 0, 0, 0)
		get_BMR = calculate_BMR(profile)
		self.assertEqual(1595, round(get_BMR, 0))
		profile = Profile(110, 5, 0, '10/01/1991', 'M', 'A', 'L2',
		                   0, 0, 0, 0, 0, 0)
		get_BMR = calculate_BMR(profile)
		self.assertEqual(2060, round(get_BMR, 0))
	
	@freeze_time("2017-05-29")	
	def test_net_calories(self):
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'S', 'L2',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(1200, round(get_net_calories, 2))
		profile = Profile(110, 5, 0, '10/01/1991', 'M', 'S', 'L2',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(1500, round(get_net_calories, 2))
		profile = Profile(110, 5, 0, '10/01/1991', 'M', 'A', 'L1',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(1560.0, get_net_calories)
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'A', 'L1',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(1303.0, get_net_calories)
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'A', 'G.5',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(2053.0, get_net_calories)
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'A', 'G1',
		                    0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(2303.0, get_net_calories)
		
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'A', 'M',
		                   0, 0, 0, 0, 0, 0)
		get_net_calories = calculate_net_calories(profile)
		self.assertEqual(1803.0, get_net_calories)
		
		
	def test_get_nutrient_goals(self):
		profile = Profile(110, 5, 0, '10/01/1991', 'F', 'A', 'M',
		                   1803, 0, 0, 0, 0, 0)
		get_nutrient_goals(profile)
		self.assertEqual(225.375, profile.carbs)
		self.assertEqual(60.1, round(profile.fat, 1))
		self.assertEqual(90.15, round(profile.protein, 2))
		self.assertEqual(2300, profile.sodium)
		self.assertEqual(45, profile.sugar)
	
	@freeze_time("2017-05-29")	
	def test_update_user_profile_model(self):
		profile_form_data = {
			'weight': 110,
			'height_ft': 5,
			'height_in': 0,
			'goal_weight': 104,
			'gender': 'F',
			'birth_date': '10/01/1991',
			'zip_code': 10005,
			'lifestyle': 'VA',
			'workouts_week': 0,
			'min_per_workout': 30,
			'goal': 'L1',
		}
		response = self.client.post('/polls/user_profile/', profile_form_data)
		get_class = SetUp_Class()
		get_profile = UserProfile.objects.get(user=self.user)
		self.assertEqual(get_profile.weight, 110)
		self.assertEqual(get_profile.goal_weight, 104)
		self.assertEqual(get_profile.min_per_workout, 30)
		self.assertEqual(get_profile.net_calories, 1506)
		self.assertEqual(get_profile.carbs, 188.25)
		self.assertEqual(get_profile.fat, 50.2)
		
	@freeze_time("2017-05-29")	
	def test_correct_variables_user_profile_template(self):
		profile_form_data = {
			'weight': 110,
			'height_ft': 5,
			'height_in': 0,
			'goal_weight': 104,
			'gender': 'F',
			'birth_date': '10/01/1991',
			'zip_code': 10005,
			'lifestyle': 'VA',
			'workouts_week': 0,
			'min_per_workout': 30,
			'goal': 'L1',
		}
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertContains(response, "1506.0 Calories / Day")
		self.assertContains(response, "0")
		self.assertContains(response, "30")
		self.assertContains(response, "If you follow this plan, your projected weight loss is ")
		self.assertContains(response, "1.0 pound/week. <br>")
		self.assertContains(response, "You should lose 5.0 lbs by")
	
	@freeze_time("2017-05-29")	
	def test_correct_variables_user_profile_template_gain_weight(self):
		profile_form_data = {
			'weight': 110,
			'height_ft': 5,
			'height_in': 0,
			'goal_weight': 104,
			'gender': 'F',
			'birth_date': '10/01/1991',
			'zip_code': 10005,
			'lifestyle': 'VA',
			'workouts_week': 0,
			'min_per_workout': 30,
			'goal': 'G1',
		}
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertContains(response, "2506.0 Calories / Day")
		self.assertContains(response, "If you follow this plan, your projected weight gain is ")
		self.assertContains(response, "1.0 pound/week. <br>")
		self.assertContains(response, "You should gain 5.0 lbs by")
		
	@freeze_time("2017-05-29")
	def test_correct_variables_user_profile_template_sedentary_lose_two(self):
		profile_form_data = {
			'weight': 110,
			'height_ft': 5,
			'height_in': 0,
			'goal_weight': 104,
			'gender': 'F',
			'birth_date': '10/01/1991',
			'zip_code': 10005,
			'lifestyle': 'S',
			'workouts_week': 0,
			'min_per_workout': 30,
			'goal': 'L2',
		}
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertContains(response, "1200 Calories / Day")
		self.assertContains(response, "If you follow this plan, your projected weight loss is ")
		self.assertContains(response, "0.39 pounds/week. <br>")
		self.assertContains(response, "You should lose 2.0 lbs by")
		
	def test_five_weeks_from_now(self):
		today = datetime.datetime.strptime("5/29/2017", '%m/%d/%Y').date()
		five_weeks = today + datetime.timedelta(days=35)
		five_weeks = five_weeks.strftime("%B %d, %Y")
		self.assertEqual(five_weeks, "July 03, 2017")
	
	@freeze_time("2017-05-29")	
	def test_actual_five_weeks_from_now_function(self):
		five_weeks = five_weeks_from_now()
		self.assertEqual(five_weeks, "July 03, 2017")
		
	def test_get_started_link(self):
		valid_form = change_form_data_and_run_form('weight', 110)
		response = self.client.post('/polls/user_profile/', profile_form_data)
		self.assertContains(response, '<a href="%s" class="button" style="position: relative; left:250px;">Get Started Now</a>' 
		                     % reverse("polls:index"), html=True)
		#print(response.content)
		
class Profile(object):

	def __init__(self, weight, height_ft, height_in, birth_date, gender, lifestyle, goal,
	             net_calories, carbs, fat, protein, sodium, sugar):
		self.weight = weight
		self.height_ft = height_ft
		self.height_in = height_in
		self.birth_date = datetime.datetime.strptime(birth_date, '%m/%d/%Y').date()
		self.gender = gender
		self.lifestyle = lifestyle
		self.goal = goal
		self.net_calories = net_calories
		self.carbs = carbs
		self.fat = fat
		self.protein = protein
		self.sodium = sodium
		self.sugar = sugar
		
class FoodTest(TestCase):

		
	def setUp(self):
		global today
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.client.login(username='jacob', password='top_secret')
		self.user = user
		birth_date = datetime.datetime.strptime('10/1/2013', '%m/%d/%Y').date()
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 1), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		today = "2017-05-30"
		
	
	@freeze_time("2017-05-30")		
	def test_food_redirect(self):
		response = self.client.get('/polls/food/')
		string_url = "/polls/" + today + "/update_food_diary/"
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, string_url)
		
	def test_create_user_days(self):
		get_date = datetime.datetime.strptime("5/30/2017", '%m/%d/%Y').date()
		create_user_days_record(self.user, get_date)
		get_days = UserDays.objects.get(date=get_date, user=self.user)
		self.assertFalse(get_days.done)
		
	def test_user_days_already_exists(self):
		get_date = datetime.datetime.strptime("5/30/2017", '%m/%d/%Y').date()
		create_user_days_record(self.user, get_date)
		create_user_days_record(self.user, get_date)
		get_days = UserDays.objects.filter(date=get_date, user=self.user).count()
		self.assertEqual(get_days, 1)
		
	def test_initial_quicktools_set_to_false(self):
		response = self.client.get('/polls/food/', follow=True)
		self.assertTemplateUsed(response, 'polls/food.html')
		self.assertNotContains(response, "Close Quick Tools", html=True)
		
	def test_user_days_done_false(self):
		response = self.client.get('/polls/food/', follow=True)
		self.assertTemplateUsed(response, 'polls/food.html')
		self.assertContains(response, """<p><b>When you've finished logging all foods and exercise 
									for this day, click here:</b></p>""", html=True)
									
	def test_no_user_meals_records_new_day(self):
		response = self.client.get('/polls/food/', follow=True)
		get_user_meals = UserMeals.objects.filter(user=self.user, date=today).count()
		self.assertEqual(get_user_meals, 0)
		
	def test_query_daily_goals(self):
		get_user_profile = query_daily_goals(self.user)
		expected = [1200, 150, 40, 60, 2300, 45]
		self.assertEqual(get_user_profile, expected)
		
	def test_get_remaining(self):
		query_totals = [899.5, 120, 20, 20, 2100, 40]
		user_profile = [1200, 150, 40, 60, 2300, 45]
		expected = [300.5, 30, 20, 40, 200, 5]
		subtracted_values = get_remaining(query_totals, user_profile)
		self.assertEqual(expected, subtracted_values)
	
	@freeze_time("2017-05-30")
	def test_projected_weight(self):
		get_projected_weight = projected_weight(self.user, "2017-05-30")
		self.assertEqual(96, round(get_projected_weight, 0))
	
	@freeze_time("2017-05-30")		
	def test_template_variables_food_to_food_diarly(self):
		response = self.client.get('/polls/food/', follow=True)
		self.assertContains(response, "2017-05-30")
		#print(response.content)
		self.assertContains(response, "Breakfast")
		self.assertContains(response, "Lunch")
		self.assertContains(response, "Dinner")
		self.assertContains(response, "Snacks")
		self.assertContains(response, "<td style='text-align:center;'><b>1200.0</b></td>", html=True)
		self.assertContains(response, "<td style='text-align:center;'><b>150.0</b></td>", html=True)
		
	@freeze_time("2017-05-30") 
	def test_update_food_diary_template_links(self):
		response = self.client.get('/polls/food/', follow=True)
		#print(response.content)
		self.assertContains(response, '<a href="%s">&#8678;</a>' % reverse("polls:yesterday_food", kwargs={'today': today}), html=True)
		self.assertContains(response, '<a href="%s">&#8680;</a>' % reverse("polls:tomorrow_food", kwargs={'today': today}), html=True)
		self.assertContains(response, '<a href="%s">Add Food | </a>' % reverse("polls:add_food", 
		                    kwargs={'today': today, 'name': 'Breakfast'}), html=True)
		self.assertContains(response, '<a href="%s">Quick Tools</a>' % reverse("polls:quick_tools_open", 
		                    kwargs={'today': today, 'name': 'Breakfast'}), html=True)
		self.assertContains(response, """<a href="%s" class="button" style=" position: relative; left:250px; font-size: medium">Complete This Entry</a>"""
							  % reverse("polls:completed_entry", kwargs={'today': today}), html=True)
							  
class AddFoodTest(TestCase):

	def setUp(self):
		global today
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.client.login(username='jacob', password='top_secret')
		self.user = user
		birth_date = datetime.datetime.strptime('10/1/2013', '%m/%d/%Y').date()
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=birth_date, country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		today = datetime.date.today()
		today = str(today)
		user_days = UserDays.objects.create(user=self.user, date=today, done=False)
		FoodDatabase.objects.create(food='Banana', calories=110, serving_size=1, units='banana')
		FoodDatabase.objects.create(food='Fiber One Bar', calories=140, serving_size=40, units='grams')
		FoodDatabase.objects.create(food='Quick Add', calories=1, serving_size=1, units='calorie')
		
	def test_query_all_usermeals(self):
		response = self.client.get('/polls/2017-05-30/Breakfast/add_food/', follow=True)
		get_user_meals = UserMeals.objects.filter(user=self.user, date=today).count()
		self.assertEqual(get_user_meals, 0)
		
	def test_recent_query_and_frequent_query(self):
		recent_query = query_recent_meals(self.user)
		self.assertFalse(recent_query)
		frequent_query = query_frequent_meals(self.user)
		self.assertFalse(frequent_query)
		
	def test_get_meals_no_records(self):
		response = self.client.get('/polls/2017-05-30/Breakfast/add_food/', follow=True)
		get_remembered_meals = RememberMeals.objects.filter(user=self.user).count()
		self.assertEqual(get_remembered_meals, 0)
		
	def test_template_add_food(self):
		response = self.client.get('/polls/2017-05-30/Breakfast/add_food/', follow=True)
		self.assertTemplateUsed(response, 'polls/add_food.html')
		
def create_food_database_objects():
	FoodDatabase.objects.get_or_create(food='Banana', calories=110, serving_size=1, units='banana', carbs=27,
		                             fat=.4, protein=1.3, sodium=1, sugar=14)
	FoodDatabase.objects.get_or_create(food='Fiber One Bar', calories=140, serving_size=40, units='grams',
									carbs=29, fat=4, protein=2, sodium=90, sugar=10)
	FoodDatabase.objects.get_or_create(food='Half and Half', calories=20, serving_size=1, units='TBSP')
	FoodDatabase.objects.get_or_create(food='Quick Add', calories=1, serving_size=1, units='calorie')
	FoodDatabase.objects.get_or_create(food='Strawberry - Medium', calories=4, serving_size=9, units='ounces')
	FoodDatabase.objects.get_or_create(food='Fiber Brownie', calories=85, serving_size=22, units='GMs')
	FoodDatabase.objects.get_or_create(food='Orange', calories=69, serving_size=7.3, units='oz')
	FoodDatabase.objects.get_or_create(food='1% Milk', calories=206, serving_size=2, units='cups')
	FoodDatabase.objects.get_or_create(food='2% Milk', calories=15, serving_size=1, units='fl oz')
	FoodDatabase.objects.get_or_create(food='Honey', calories=42, serving_size=2, units='Teaspoons')
	FoodDatabase.objects.get_or_create(food='Peanut Butter', calories=188, serving_size=2, units='Tablespoons')
		
class SearchFoodTest(TestCase):

	def setUp(self):
		global today, simple_volume, user
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		self.client.login(username='jacob', password='top_secret')
		self.user = user
		birth_date = datetime.datetime.strptime('10/1/2013', '%m/%d/%Y').date()
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=birth_date, country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		today = datetime.date.today()
		today = str(today)
		user_days = UserDays.objects.create(user=self.user, date=today, done=False)
		create_food_database_objects()
		simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
		
	
		
	def get_database_units(self, selected):
		database_units_1 = selected.units.lower().strip().rstrip("s")
		convert_database_units = {
		'teaspoon': 'tsp',
		'tablespoon': 'tbsp',
		'fl oz': 'fluid ounce',
		}
		try:
			database_units = convert_database_units.get(database_units_1)
		except:
			database_units = 1
		if not database_units:
			database_units = database_units_1
		return database_units
		
	def test_search_food_query_food_database(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		get_food_items = FoodDatabase.objects.count()
		self.assertEqual(get_food_items, 11)
		
	def test_selected_gets_correct_food_item(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		get_food_selected = FoodDatabase.objects.get(food='Banana')
		self.assertEqual(get_food_selected.food, 'Banana')
		
	def test_search_function_renders_correct_template(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertTemplateUsed(response, 'polls/search_food.html')
		
	def test_search_food_template_does_not_show_quick_add(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertNotContains(response, "Quick Add")
		
	def test_search_food_template_get_doesnt_have_add_to_(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertNotContains(response, "Add to")
		
	def test_search_template_contains_correct_food_items(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertContains(response, "Banana")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Half and Half")
		
	def test_search_template_contains_correct_serving_sizes(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertContains(response, "1.0 banana")
		self.assertContains(response, "40.0 gram")
		self.assertContains(response, "1.0 TBSP")
		
	def test_search_template_contains_correct_calorie_counts(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertContains(response, "110.0 calories")
		self.assertContains(response, "140.0 calories")
		self.assertContains(response, "20.0 calories")
		
	def test_link_add_food_to_database(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertContains(response, "<a href=%s>Add a food to the database</a>" % reverse("polls:add_food_to_database"), html=True)
		
	def test_search_template_select_link(self):
		response = self.client.get('/polls/none/2017-05-30/search_food/', follow=True)
		self.assertContains(response, "<a href=%s>Select</a>" % reverse("polls:search_food", 
		                      kwargs={'food': 'Banana', 'today':'2017-05-30'}), html=True)
							  
	def test_user_meal_form_valid(self):
		form_data = {'servings': 2.0, 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_user_meal_invalid_serving(self):
		form_data = {'servings': 'candy', 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertFalse(form.is_valid())
		form_data = {'servings': '-5', 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertFalse(form.is_valid())
		form_data = {'servings': '0', 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_user_meal_servings_is_float(self):
		form_data = {'servings': 1.6789, 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertTrue(form.is_valid())
		
	def test_user_meal_meal_is_not_a_choice(self):
		form_data = {'servings': 1.6789, 'meals': 'Q', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		form = UserMealsForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_calculate_portions_1_banana(self):
		selected = FoodDatabase.objects.get(food='Banana')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(3.7, 'banana', 1.0, selected, database_units, simple_volume)
		self.assertEqual(3.7, portion)
		
	def test_calculated_portions_fiber_bars(self):
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(3.7, 'gram', 40.0, selected, database_units, simple_volume)
		self.assertEqual(3.7, portion)
		
	def test_calculated_portions_1_gram_fiber_bar(self):
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(3.7, 'gram', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.0925, portion)
		
	def test_calculated_portions_1_ounce_fiber_bar(self):
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		database_units = self.get_database_units(selected)
		print("database units: ", database_units)
		portion = calculate_portions(3.7, 'ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(2.622, round(portion, 3))
		
	def test_calculated_portions_strawberry(self):
		selected = FoodDatabase.objects.get(food='Strawberry - Medium')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(100, 'gram', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.392, round(portion, 3))
		
	def test_calculated_portions_gms(self):
		selected = FoodDatabase.objects.get(food='Fiber Brownie')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(50, 'gram', 1.0, selected, database_units, simple_volume)
		self.assertEqual(2.273, round(portion, 3))
		
	def test_calculated_portions_gms_to_ounces(self):
		selected = FoodDatabase.objects.get(food='Fiber Brownie')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(10, 'ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(12.886, round(portion, 3))
		
	def test_calculated_portions_oz_to_ounces(self):
		selected = FoodDatabase.objects.get(food='Orange')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(10, 'ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(1.370, round(portion, 3))
		
	def test_calculated_portions_oz_to_grams(self):
		selected = FoodDatabase.objects.get(food='Orange')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(100, 'gram', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.483, round(portion, 3))
		
	def test_calculated_portions_tbsp_quantities(self):
		selected = FoodDatabase.objects.get(food='Half and Half')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(4, 'tbsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(4, portion)
		portion = calculate_portions(4, 'tsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(1.33, round(portion, 2))
		portion = calculate_portions(.2, 'cup', 1.0, selected, database_units, simple_volume)
		self.assertEqual(3.2, round(portion, 2))
		portion = calculate_portions(4, 'fluid ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(8, round(portion, 2))
		
	def test_calculated_portions_milk_quantities(self):
		selected = FoodDatabase.objects.get(food='1% Milk')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(10, 'tsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.104, round(portion, 3))
		portion = calculate_portions(10, 'tbsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.312, round(portion, 3))
		portion = calculate_portions(10, 'fluid ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(.625, round(portion, 3))
		portion = calculate_portions(10, 'cup', 1.0, selected, database_units, simple_volume)
		self.assertEqual(5, round(portion, 2))
		
	def test_calculated_portions_2_percent_milk(self):
		selected = FoodDatabase.objects.get(food='2% Milk')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(10, 'tsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(1.67, round(portion, 2))
		portion = calculate_portions(10, 'tbsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(5, round(portion, 3))
		portion = calculate_portions(10, 'fluid ounce', 1.0, selected, database_units, simple_volume)
		self.assertEqual(10, round(portion, 3))
		portion = calculate_portions(10, 'cup', 1.0, selected, database_units, simple_volume)
		self.assertEqual(80, round(portion, 2))
		
	def test_calculate_portions_teaspoon(self):
		selected = FoodDatabase.objects.get(food='Honey')
		database_units = self.get_database_units(selected)
		portion = calculate_portions(10, 'tbsp', 1.0, selected, database_units, simple_volume)
		self.assertEqual(15, round(portion, 2))
		
	def test_volume_conversions(self):
		get_volume = volume_conversions(10, 'tsp', 'tbsp')
		self.assertEqual(3.33, round(get_volume, 2))
		get_volume = volume_conversions(10, 'tbsp', 'tsp')
		self.assertEqual(30, round(get_volume, 2))
		get_volume = volume_conversions(10, 'tsp', 'fluid ounce')
		self.assertEqual(1.67, round(get_volume, 2))
		get_volume = volume_conversions(10, 'fluid ounce', 'tsp')
		self.assertEqual(60, round(get_volume, 2))
		get_volume = volume_conversions(10, 'tbsp', 'cup')
		self.assertEqual(.62, round(get_volume, 2))
		get_volume = volume_conversions(10, 'cup', 'tbsp')
		self.assertEqual(160, round(get_volume, 2))
		
	
	def test_create_database_record_banana(self):
		selected = FoodDatabase.objects.get(food='Banana')
		today = "2017-05-30"
		today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
		create_database_record(selected, 1, "banana", "B", 3, today, self.user, 3 )
		query_record = UserMeals.objects.get(user=self.user)
		self.assertTrue(query_record)
		self.assertEqual(query_record.date, today)
		self.assertEqual(query_record.user, self.user)
		self.assertEqual(query_record.meal_type, "B")
		self.assertEqual(query_record.food_item.food, "Banana")
		self.assertEqual(query_record.portion, 3)
		self.assertEqual(query_record.units_consumed, 3)
		self.assertEqual(query_record.units, "banana")
		self.assertEqual(query_record.cal_eaten, 330)
		self.assertEqual(query_record.carbs, 81)
		self.assertEqual(round(query_record.fat, 1), 1.2)
		self.assertEqual(round(query_record.protein, 1), 3.9)
		self.assertEqual(query_record.sodium, 3)
		self.assertEqual(query_record.sugar, 42)
		
	def test_create_database_record_fiber_one_bar(self):
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		today = "2017-05-31"
		today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
		create_database_record(selected, 1, "ounce", "S", 1.4175, today, self.user, 2 )
		query_record = UserMeals.objects.get(user=self.user)
		self.assertTrue(query_record)
		self.assertEqual(query_record.date, today)
		self.assertEqual(query_record.user, self.user)
		self.assertEqual(query_record.meal_type, "S")
		self.assertEqual(query_record.food_item.food, "Fiber One Bar")
		self.assertEqual(query_record.portion, 1.4175)
		self.assertEqual(query_record.units_consumed, 2)
		self.assertEqual(query_record.units, "ounce")
		self.assertEqual(query_record.cal_eaten, 198.45)
		self.assertEqual(query_record.carbs, 41.1075)
		self.assertEqual(round(query_record.fat, 2), 5.67)
		self.assertEqual(round(query_record.protein, 3), 2.835)
		self.assertEqual(query_record.sodium, 127.575)
		self.assertEqual(query_record.sugar, 14.175)
		
		
class SearchFoodRedirectTest(TestCase):

	
	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		user = User.objects.create_user('jacob13', 'jacob@gmail.com', 'top_secret')
		self.client.login(username='jacob13', password='top_secret')
		self.user = user
		birth_date = datetime.datetime.strptime('10/1/1991', '%m/%d/%Y').date()
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 10), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		date_today = datetime.date(2017, 5, 30)
		string_today = str(date_today)
		user_days = UserDays.objects.create(user=self.user, date=datetime.date(2017, 5, 30), done=False)
		create_food_database_objects()
		simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
		self.CreateUserMeals()
		
	def CreateUserMeals(self):
		selected = FoodDatabase.objects.get(food="Banana")
		create_database_record(selected, 1, "banana", "B", 3, string_today, self.user, 3 )
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(selected, 1, "ounce", "S", 1.4175, string_today, self.user, 2 )
		
		
	def test_search_food_redirect(self):
		form_data = {'servings': 2.0, 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		response = self.client.post('/polls/Banana/2017-05-30/search_food/', form_data, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'polls/food.html')
		
	def test_view_selected_food(self):
		response = self.client.get("/polls/Fiber%20One%20Bar/2017-06-02/search_food/")
		self.assertContains(response, "40.0 grams")
		self.assertContains(response, "<option value='1 ounce'>1 oz</option>", html=True)
		self.assertContains(response, "<option value='1 gram'>1 gram</option>", html=True)
		
	def test_view_selected_food_volume_based(self):
		response = self.client.get("/polls/Honey/2017-06-02/search_food/")
		self.assertContains(response, "40.0 grams")
		self.assertContains(response, "<option value='1 cup'>1 cup</option>", html=True)
		self.assertContains(response, "<option value='1 tbsp'>1 tbsp</option>", html=True)
		self.assertContains(response, "<option value='1 fluid ounce'>1 fluid ounce</option>", html=True)
		self.assertContains(response, "<option value='1 tsp'>1 tsp</option>", html=True)
		
	def test_post_form_data_check_template(self):
		form_data = {'servings': 2.0, 'meals': 'D', "serve_size": '1.0 fluid ounce', 
                     'food': 'Half and Half', 'today': '2017-05-30'}
		response = self.client.post('/polls/Half and Half/2017-05-30/search_food/', form_data, follow=True)
		#print(response.content)
		self.assertContains(response, "2.0 fluid ounces")
		self.assertContains(response, "80.0")
		
	def test_query_database_records(self):
		#today = datetime.datetime.strptime("2017-05-30", '%Y-%m-%d').date()
		query_database_records(date_today, self.user)
		
	def test_convert_query_sums_cal_eaten_1000(self):
		sum_info = {'cal_eaten__sum': 1000}
		a = convert_query_sums(sum_info, 'cal_eaten')
		self.assertEqual(a, 1000)
		sum_info = {}
		a = convert_query_sums(sum_info, 'cal_eaten')
		self.assertEqual(a, " ")
		sum_info = {'cal_eaten__sum': 0.0}
		a = convert_query_sums(sum_info, 'cal_eaten')
		self.assertEqual(a, 0)
		
	def test_get_query_totals(self):
		query_totals = get_query_totals(self.user, date_today)
		query_totals_new = []
		for q in query_totals:
			q = round(q, 2)
			query_totals_new.append(q)
		self.assertEqual([528.45, 122.11, 6.87, 6.74, 130.57, 56.17], query_totals_new)
		
	def test_query_sums(self):
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(selected, 1, "gram", "S", .5, string_today, self.user, 20)
		create_database_record(selected, 40, "grams", "B", 3, string_today, self.user, 3 )
		form_data = {'servings': 3.0, 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		response = self.client.post('/polls/Banana/2017-05-30/search_food/', form_data, follow=True)
		self.assertContains(response, "1080")
		self.assertContains(response, "268.4")
		self.assertContains(response, "249")
		self.assertContains(response, "14.4")
		self.assertContains(response, "55.6")
		self.assertContains(response, "5.7")
		
	def test_projected_weight(self):
		project_weight = projected_weight(self.user, date_today)
		self.assertEqual(round(project_weight, 2), 101.33)
		
	def test_search_food_to_food_template_variables(self):
		form_data = {'servings': 2.0, 'meals': 'B', "serve_size": '1.0 banana', 
                     'food': 'Banana', 'today': '2017-05-30'}
		response = self.client.post('/polls/Banana/2017-05-30/search_food/', form_data, follow=True)
		self.assertContains(response, "2017-05-30")
		self.assertContains(response, "Banana")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "2.0")
		self.assertContains(response, "3.0")
		self.assertContains(response, "bananas")
		self.assertContains(response, "330.0")
		self.assertContains(response, "81.0")
		self.assertContains(response, "1.2")
		self.assertContains(response, "3.9")
		self.assertContains(response, "3.0")
		self.assertContains(response, "42.0")
		self.assertContains(response, "198")
		self.assertContains(response, "41")
		self.assertContains(response, "5.7")
		self.assertContains(response, "2.8")
		self.assertContains(response, "127.6")
		self.assertContains(response, "14.2")
		self.assertContains(response, "550")
		self.assertContains(response, "135")
		self.assertNotContains(response, "Close Quick Tools")
		self.assertContains(response, "When you've finished logging all foods")
		self.assertContains(response, "748")
		self.assertContains(response, "176")
		self.assertContains(response, "1200")
		#print(response.content)
		self.assertContains(response, "451.5")
		self.assertContains(response, "-26.1")
		
class DeleteMealCompleteEntriesDatesTest(TestCase):

	
	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		self.factory = RequestFactory()
		user = User.objects.create_user('jacob10', 'jacob@gmail.com', 'top_secret')
		self.user = user
		self.client.login(username='jacob10', password='top_secret')
		
		birth_date = datetime.datetime.strptime('10/1/1991', '%m/%d/%Y').date()
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 1), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		date_today = datetime.date(2017, 5, 30)
		string_today = str(date_today)
		user_days = UserDays.objects.create(user=user, date=datetime.date(2017, 5, 30), done=False)
		create_food_database_objects()
		simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
		selected = FoodDatabase.objects.get(food="Banana")
		create_database_record(selected, 1, "banana", "B", 3, "2017-05-30", user, 3 )
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(selected, 1, "ounce", "S", 1.4175, "2017-05-30", user, 2 )
		
		
	def test_delete_fiber_meal(self):
		get_query = UserMeals.objects.get(user=user, date=date_today, meal_type="S")
		q = get_query.id
		response = self.client.get("/polls/2017-05-30/2/delete_user_meal/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertNotContains(response, "198")
		self.assertContains(response, "330")
		self.assertNotContains(response, "Fiber")
		query_set = UserMeals.objects.filter(user=user).count()
		self.assertEqual(query_set, 1)
		
	def test_delete_resets_quicktools(self):
		response = self.client.get("/polls/2017-05-30/Breakfast/quick_tools_open/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Close Quick Tools")
		get_query = UserMeals.objects.get(date=date_today, meal_type="S")
		banana_query = UserMeals.objects.get(date=date_today, meal_type="B")
		banana_id = banana_query.id
		q = get_query.id
		response = self.client.get("/polls/2017-05-30/2/delete_user_meal/", follow=True)
		self.assertNotContains(response, "Close Quick Tools")
		self.assertContains(response, '<a href="%s">Delete</a>' % reverse("polls:delete_user_meal", 
		                                                          kwargs={'q': banana_id, 'today': '2017-05-30'}), html=True)
		
		
	def test_done_status(self):
		user_date_combo = get_done_status(user, date_today, True)
		get_done = user_date_combo.done
		self.assertTrue(get_done)
		
	def test_complete_entry_under_calorie_count(self):
		response = self.client.get("/polls/2017-05-30/completed_entry/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Based on your total calories consumed for today,")
		self.assertContains(response, "you are likely not eating enough.")
		self.assertContains(response, "Make Additional Entries")
		self.assertContains(response, '<a href="%s" class="button" style="position: relative; left:250px; font-size: medium">Make Additional Entries</a>' % 
		                                 reverse("polls:make_additional_entries", kwargs={'today': '2017-05-30'}), html=True)
		
	def test_make_additional_entries(self):
		response = self.client.get("/polls/2017-05-30/make_additional_entries/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "When you've finished logging all foods and exercise")
		self.assertContains(response, "Complete This Entry")
	
	@freeze_time("2017-05-30")
	def test_complete_entry_over_calorie_count(self):
		selected = FoodDatabase.objects.get(food="Banana")
		create_database_record(selected, 1, "banana", "B", 5, string_today, self.user, 5)
		response = self.client.get("/polls/2017-05-30/completed_entry/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "<p>If every day were like today, you'd weigh...")
		self.assertContains(response, "Make Additional Entries")
		self.assertContains(response, "106.8 lbs")
		
	def test_yesterday(self):
		response = self.client.get("/polls/2017-05-30/yesterday_food/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "2017-05-29")
		self.assertNotContains(response, "2017-05-30")
		yesterday = datetime.date(2017, 5, 29)
		get_date = UserDays.objects.filter(user=self.user, date=yesterday).count()
		self.assertEqual(1, get_date)
		self.assertNotContains(response, "Close")
		self.assertNotContains(response, "Banana")
		self.assertNotContains(response, "Fiber")
		
	def test_tomorrow(self):
		response = self.client.get("/polls/2017-05-30/tomorrow_food/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "2017-05-31")
		self.assertNotContains(response, "2017-05-30")
		tomorrow = datetime.date(2017, 5, 31)
		get_date = UserDays.objects.filter(user=self.user, date=tomorrow).count()
		self.assertEqual(1, get_date)
		self.assertNotContains(response, "Close")
		self.assertNotContains(response, "Banana")
		self.assertNotContains(response, "Fiber")
		
	def cleanUp(self):
		reset_quicktools()
		

		
class QuickToolsTest(TestCase):

	def setUp(self):
		global date_today, string_today, simple_volume, user, user_profile
		user = User.objects.create_user('jacob', 'jacob@gmail.com', 'top_secret')
		#self.user = user
		self.client.login(username='jacob', password='top_secret')
		user_profile = UserProfile.objects.create(user=user, weight=110, height_ft=5, height_in=0,
		                goal_weight=104, gender='F', birth_date=datetime.date(1991, 10, 13), country='US', zip_code=20902,
						lifestyle='S', workouts_week=0, min_per_workout=0, goal='L2', net_calories=1200,
						carbs=150, fat=40, protein=60, sodium=2300, sugar=45)
		date_today = datetime.date(2017, 5, 30)
		string_today = "2017-05-30"
		UserDays.objects.create(user=user, date=date_today, done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 5, 31), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 5, 29), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 5, 28), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 6, 3), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 6, 1), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 6, 5), done=False)
		UserDays.objects.create(user=user, date=datetime.date(2017, 6, 6), done=False)
		create_food_database_objects()
		simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
		selected = FoodDatabase.objects.get(food="Banana")
		create_database_record(selected, 1, "banana", "B", 3, "2017-05-30", user, 3)
		create_database_record(selected, 1, "banana", "B", 3, "2017-05-31", user, 3)
		selected = FoodDatabase.objects.get(food='Fiber One Bar')
		create_database_record(selected, 1, "ounce", "S", 1.4175, "2017-05-29", user, 2)
		create_database_record(selected, 1, "gram", "D", .5, "2017-06-05", user, 20)
		selected = FoodDatabase.objects.get(food='Half and Half')
		create_database_record(selected, 1, "TBSP", "B", 2, "2017-05-31", user, 2)
		create_database_record(selected, 1, "TBSP", "D", 2, "2017-06-05", user, 2)
	
	@freeze_time("2017-05-30")
	def test_open_quicktools(self):
		response = self.client.get("/polls/2017-05-30/Breakfast/quick_tools_open/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Quick add calories")
		self.assertContains(response, "Copy from date")
		self.assertContains(response, "Copy to date")
		self.assertContains(response, "Remember Meal")
		self.assertContains(response, "Copy yesterday")
		self.assertNotContains(response, "Copy to today")
	
	@freeze_time("2017-05-30")	
	def test_quicktools_is_not_today(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Copy to today")
		self.assertNotContains(response, "Copy yesterday" )
		
	def test_quicktools_no_meals(self):
		#UserDays.objects.create(user=user, date=datetime.date(2017, 6, 1), done=False)
		response = self.client.get("/polls/2017-06-01/Breakfast/quick_tools_open/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertNotContains(response, "Remember Meal")
		
	def test_close_quick_tools(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_close/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertNotContains(response, "Remember Meal")
		self.assertNotContains(response, "Quick add calories")
		self.assertNotContains(response, "Copy from date")
		self.assertNotContains(response, "Copy to date")
		self.assertNotContains(response, "Copy yesterday")
		self.assertNotContains(response, "Copy to today")
		
	def test_quicktools_options_quick_add_calories(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/Quick add calories/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/quick_add_cal.html")
		self.assertContains(response, "<h1>Quick Add</h1>")
		self.assertContains(response, "Breakfast")
		self.assertContains(response, "Lunch")
		self.assertContains(response, "Dinner")
		self.assertContains(response, "Snacks")
		
	def test_quick_add_form_is_valid(self):
		form_data = {'servings': -5, 
						'meals': 'L'
					}
		form = QuickAddForm(data=form_data)
		self.assertFalse(form.is_valid())
		form_data = {'servings': 0, 
						'meals': 'L'
					}
		form = QuickAddForm(data=form_data)
		self.assertFalse(form.is_valid())
		form_data['servings'] = .1
		form = QuickAddForm(data=form_data)
		self.assertTrue(form.is_valid())
		form_data['meals'] = 'A'
		form = QuickAddForm(data=form_data)
		self.assertFalse(form.is_valid())
		
	def test_quick_add_form_updates_database(self):
		form_data = {'servings': 92, 
						'meals': 'D'
					}
		response = self.client.post("/polls/2017-05-30/Dinner/quick_add_calories/", form_data, follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "92.0 servings")
		self.assertNotContains(response, "Close")
		get_food_item = FoodDatabase.objects.get(food="Quick Add")
		get_query = UserMeals.objects.get(user=user, food_item=get_food_item)
		self.assertEqual(get_query.date, datetime.date(2017, 5, 30))
		self.assertEqual(get_query.meal_type, "D")
		self.assertEqual(get_query.food_item, get_food_item)
		self.assertEqual(get_query.portion, 92)
		self.assertEqual(get_query.units, "serving")
		self.assertEqual(get_query.units_consumed, 92)
		self.assertEqual(get_query.cal_eaten, 92)
		self.assertEqual(get_query.carbs, 0)
		self.assertEqual(get_query.fat, 0)
		self.assertEqual(get_query.protein, 0)
		self.assertEqual(get_query.sodium, 0)
		self.assertEqual(get_query.sugar, 0)
		
	def test_quicktools_options_copy_from_date_show_dates(self):
		#UserDays.objects.create(user=user, date=datetime.date(2017, 6, 1), done=False)
		response = self.client.get("/polls/2017-06-01/Breakfast/Copy from date/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "May 30, 2017")
		self.assertContains(response, "May 29, 2017")
		self.assertContains(response, "May 28, 2017")
		self.assertContains(response, "May 27, 2017")
		self.assertContains(response, "May 26, 2017")
		self.assertContains(response, "May 25, 2017")
		self.assertContains(response, "May 31, 2017")
		response = self.client.get("/polls/2017-06-01/Breakfast/2017-05-29/get_record_to_copy", follow=True)
		self.assertTemplateUsed("polls/food.html")
		#print(response.content)
		self.assertContains(response, "Copy from which meal?")
		self.assertNotContains(response, "Copy to which meal?")
		
	def test_quicktools_copy_from_date_update_database(self):
		copy_dates_quicktools(user, "S", datetime.date(2017, 5, 29), datetime.date(2017, 6, 1), "B")
		get_original = UserMeals.objects.get(user=user, meal_type="S", date=datetime.date(2017, 5, 29))
		get_query = UserMeals.objects.get(user=user, meal_type="B", date=datetime.date(2017, 6, 1))
		get_food_item = FoodDatabase.objects.get(food="Fiber One Bar")
		self.assertEqual(get_query.meal_type, "B")
		self.assertEqual(get_query.food_item, get_food_item)
		self.assertEqual(get_query.portion, 1.4175)
		get_query_2 = UserMeals.objects.get(user=user, date=datetime.date(2017, 5, 29), meal_type="S")
		self.assertEqual(get_query_2.food_item, get_food_item)
		self.assertEqual(get_query_2.meal_type, "S")
		
	def test_quicktools_copy_from_date_update_database_get_template(self):
		response = self.client.get("/polls/2017-06-01/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-06-01/Breakfast/Copy from date/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-06-01/Breakfast/Snacks/2017-05-29/copy_to_today", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "2017-06-01")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "2.0 ounces")
		self.assertContains(response, "198")
		self.assertNotContains(response, "Close")
		
	def test_quicktools_options_copy_to_date_get_dates(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to date/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "May 28, 2017")
		self.assertContains(response, "May 29, 2017")
		self.assertContains(response, "May 30, 2017")
		self.assertContains(response, "May 31, 2017")
		self.assertContains(response, "June 1, 2017")
		self.assertContains(response, "June 2, 2017")
		self.assertContains(response, "June 3, 2017")
		
	def test_quicktools_copy_to_date_update_template_get_meal(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to date/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/2017-05-28/get_record_to_copy", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Copy to which meal?")
		self.assertNotContains(response, "Copy from which meal?")
		
	def test_copy_to_date_create_database_record(self):
		copy_dates_quicktools(user, "B", datetime.date(2017, 5, 31), datetime.date(2017, 5, 28), "L")
		get_food_item = FoodDatabase.objects.get(food="Banana")
		get_query_items = UserMeals.objects.filter(user=user, date=datetime.date(2017, 5, 28), meal_type="L")
		get_query = get_query_items[0]
		self.assertEqual(get_query.meal_type, "L")
		self.assertEqual(get_query.food_item, get_food_item)
		self.assertEqual(get_query.portion, 3)
		get_food_2 = FoodDatabase.objects.get(food="Half and Half")
		get_query_2 = get_query_items[1]
		self.assertEqual(get_query_2.portion, 2)
		self.assertEqual(get_query_2.food_item, get_food_2)
		# check original is still there
		get_query_filter = UserMeals.objects.filter(user=user, date=datetime.date(2017, 5, 31), meal_type="B")
		get_query_2 = get_query_filter[0]
		self.assertEqual(get_query_2.food_item, get_food_item)
		self.assertEqual(get_query_2.meal_type, "B")
		
	def test_copy_to_date_template_updated_after_database(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to date/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/2017-05-28/get_record_to_copy", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/Lunch/2017-05-28/copy_to_today", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "2017-05-31")
		self.assertContains(response, "Banana")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "3.0 bananas")
		self.assertContains(response, "330")
		self.assertNotContains(response, "Close")
		response = self.client.get("/polls/2017-05-28/update_food_diary/")
		self.assertContains(response, "2017-05-28")
		self.assertContains(response, "Banana")
		self.assertContains(response, "3.0 bananas")
		self.assertContains(response, "330")
		self.assertContains(response, "Half and Half")
		
	@freeze_time("2017-06-06")
	def test_quicktools_options_copy_to_today_asks_which_meal(self):
		#UserDays.objects.create(user=user, date=datetime.date(2017, 6, 3), done=False)
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to today/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Copy to which meal?")
		self.assertNotContains(response, "Copy from which meal?")
	
	@freeze_time("2017-06-06")	
	def test_quicktools_copy_to_date_create_record(self):
		copy_dates_quicktools(user, "B", datetime.date(2017, 5, 31), datetime.date(2017, 6, 3), "D")
		get_food_item = FoodDatabase.objects.get(food="Banana")
		get_query_filter = UserMeals.objects.filter(user=user, date=datetime.date(2017, 6, 3), meal_type="D")
		get_query = get_query_filter[0]
		self.assertEqual(get_query.meal_type, "D")
		self.assertEqual(get_query.food_item, get_food_item)
		self.assertEqual(get_query.portion, 3)
		# original still there - copied, not transferred
		get_query_filter = UserMeals.objects.filter(user=user, date=datetime.date(2017, 5, 31), meal_type="B")
		get_query_2 = get_query_filter[0]
		self.assertEqual(get_query_2.food_item, get_food_item)
		self.assertEqual(get_query_2.meal_type, "B")
	
	@freeze_time("2017-06-06")	
	def test_quicktools_copy_to_today_updates_template_for_records_copied(self):
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/")
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to today/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/Dinner/2017-06-03/copy_to_today", follow=True)
		self.assertTemplateUsed("polls/food.html")
		# goes to original, original still the same
		self.assertContains(response, "2017-05-31")
		self.assertContains(response, "Banana")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "3.0 bananas")
		self.assertContains(response, "330")
		self.assertNotContains(response, "Close")
		response = self.client.get("/polls/2017-06-03/update_food_diary/")
		self.assertContains(response, "2017-06-03")
		self.assertContains(response, "Banana")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "3.0 bananas")
		self.assertContains(response, "330")
		
	@freeze_time("2017-06-06")
	def test_quicktools_options_copy_yesterday_asks_which_meal(self):
		response = self.client.get("/polls/2017-06-06/Snacks/quick_tools_open/")
		response = self.client.get("/polls/2017-06-06/Snacks/Copy yesterday/quicktools_options/", follow=True)
		self.assertTemplateUsed("polls/food.html")
		self.assertContains(response, "Copy from which meal?")
		self.assertNotContains(response, "Copy to which meal?")
		
	@freeze_time("2017-06-06")	
	def test_quicktools_copy_yesterday_create_record(self):
		copy_dates_quicktools(user, "D", datetime.date(2017, 6, 5), datetime.date(2017, 6, 6), "S")
		get_food_item = FoodDatabase.objects.get(food="Fiber One Bar")
		get_query_filter = UserMeals.objects.filter(user=user, date=datetime.date(2017, 6, 6), meal_type="S")
		# Fiber Bar copied over
		get_query = get_query_filter[0]
		self.assertEqual(get_query.meal_type, "S")
		self.assertEqual(get_query.food_item, get_food_item)
		self.assertEqual(get_query.portion, .5)
		# Half and Half copied over
		get_half_and_half = FoodDatabase.objects.get(food="Half and Half")
		get_query_2 = get_query_filter[1]
		self.assertEqual(get_query_2.meal_type, "S")
		self.assertEqual(get_query_2.food_item, get_half_and_half)
		self.assertEqual(get_query_2.portion, 2)
		self.assertEqual(get_query_2.cal_eaten, 40)
		# original still there - copied, not transferred
		get_query_filter = UserMeals.objects.filter(user=user, date=datetime.date(2017, 6, 5), meal_type="D")
		get_query_3 = get_query_filter[0]
		self.assertEqual(get_query_3.food_item, get_food_item)
		self.assertEqual(get_query_3.meal_type, "D")
		
	@freeze_time("2017-06-06")	
	def test_quicktools_copy_yesterday_updates_template_for_records_copied(self):
		response = self.client.get("/polls/2017-06-06/Snacks/quick_tools_open/")
		response = self.client.get("/polls/2017-06-06/Snacks/Copy yesterday/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-06-06/Snacks/Dinner/2017-06-05/copy_to_today", follow=True)
		self.assertTemplateUsed("polls/food.html")
		#updated template
		self.assertContains(response, "2017-06-06")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "2.0 TBSPs")
		self.assertContains(response, "20.0 grams")
		self.assertContains(response, "40.0")
		self.assertContains(response, "70.0")
		self.assertNotContains(response, "Close")
		#yesteday still the same
		response = self.client.get("/polls/2017-06-05/update_food_diary/")
		self.assertContains(response, "2017-06-05")
		self.assertContains(response, "Fiber One Bar")
		self.assertContains(response, "Half and Half")
		self.assertContains(response, "2.0 TBSPs")
		self.assertContains(response, "20.0 grams")
		
	@freeze_time("2017-06-07")
	def test_reverse_links_quicktools(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-06-06/Snacks/quick_tools_open/", follow=True)
		self.assertContains(response, "<a href='%s'>Copy to date</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-06-06", "name": "Snacks", "q": "Copy to date"}), html=True)
		self.assertContains(response, "<a href='%s'>Copy to today</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-06-06", "name": "Snacks", "q": "Copy to today"}), html=True)
		self.assertContains(response, "<a href='%s'>Copy from date</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-06-06", "name": "Snacks", "q": "Copy from date"}), html=True)
		self.assertContains(response, "<a href='%s'>Quick add calories</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-06-06", "name": "Snacks", "q": "Quick add calories"}), html=True)
		
	def test_reverse_remember_meal(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/", follow=True)
		self.assertContains(response, "<a href='%s'>Remember Meal</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-05-31", "name": "Breakfast", "q": "Remember Meal"}), html=True)
	
	@freeze_time("2017-06-06")
	def test_reverse_copy_yesterday(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-06-06/Snacks/quick_tools_open/", follow=True)
		self.assertContains(response, "<a href='%s'>Copy yesterday</a>" % 
		                     reverse("polls:quicktools_options", kwargs={'today': "2017-06-06", "name": "Snacks", "q": "Copy yesterday"}), html=True)
							 
	def test_reverse_get_record_to_copy(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to date/quicktools_options/", follow=True)
		self.assertContains(response, "<a href='%s'>June 1, 2017</a>" % 
		                     reverse("polls:get_record_to_copy", kwargs={'today': "2017-05-31", "name": "Breakfast", "c": "2017-06-01"}), html=True)
							 
	def test_reverse_copy_to_today(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/Copy to date/quicktools_options/", follow=True)
		response = self.client.get("/polls/2017-05-31/Breakfast/2017-06-01/get_record_to_copy", follow=True)
		self.assertContains(response, "<a href='%s'>Snacks</a>" % 
		                     reverse("polls:copy_to_today", 
							 kwargs={'today': "2017-05-31", "name": "Breakfast", "c": "2017-06-01", "m": "Snacks"}), html=True)
							 
	def test_quicktools_close(self):
		reset_quicktools()
		response = self.client.get("/polls/2017-05-31/Breakfast/quick_tools_open/", follow=True)
		self.assertContains(response, "<a href='%s'>Close Quick Tools</a>" % 
		                     reverse("polls:quick_tools_close", 
							 kwargs={'today': "2017-05-31", "name": "Breakfast"}), html=True)
		
		