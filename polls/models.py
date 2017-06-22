import datetime

from django import forms
from django.db import models
from django.forms import ModelForm
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator



class UserProfile(models.Model):

	LIFESTYLES = (
		('S', 'Sedentary'),
		('LA', 'Lightly Active'),
		('A', 'Active'), 
		('VA', 'Very Active'),
	)
	GOAL = (
			('L2', 'Lose 2 pounds per week'),
			('L1.5', 'Lose 1.5 pound per week'), 
			('L1', 'Lose 1 pound per week'),
			('L.5', 'Lose .5 pounds per week'),
			('M', 'Maintain my current weight'), 
			('G.5', 'Gain .5 pounds per week'),
			('G1', 'Gain 1 pound per week'),
	)
	GENDER = (
			('M', 'Male'),
			('F', 'Female'),
	)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	weight = models.FloatField(validators=[MinValueValidator(.1)])
	height_ft = models.IntegerField(default=0, choices=[(x, str(x)) for x in range(1,9)])
	height_in = models.IntegerField(default=0, choices=[(x, str(x)) for x in range(0,12)])
	goal_weight = models.FloatField(validators=[MinValueValidator(.1)])
	gender = models.CharField(max_length=10, choices=GENDER)
	birth_date = models.DateField()
	country = models.CharField(max_length=100)
	zip_code = models.IntegerField(validators=[RegexValidator(regex='^.{5}$', 
	                               message='Zip code length must be 5.', code='nomatch'), MinValueValidator(1) ])
	lifestyle = models.CharField(max_length=100, choices=LIFESTYLES)
	workouts_week = models.IntegerField(default=0, choices=[(x, str(x)) for x in range(0,8)])
	min_per_workout = models.IntegerField(default=0, validators=[MinValueValidator(0)])
	goal = models.CharField(max_length=100, choices=GOAL)
	net_calories = models.FloatField(default=0)
	carbs = models.FloatField(default=0)
	fat = models.FloatField(default=0)
	protein = models.FloatField(default=0)
	sodium = models.FloatField(default=0)
	sugar = models.FloatField(default=0)
	
class UserProfileForm(ModelForm):
	

	class Meta:
		model = UserProfile
		fields = ['weight', 'height_ft', 'height_in', 'goal_weight', 'gender', 'birth_date',
		          'zip_code', 'lifestyle', 'workouts_week', 'min_per_workout',
				  'goal']
	
class FoodDatabase(models.Model):

	UNITS = (
		('grams', 'grams'),
		('ounces', 'ounces'),
		('cups', 'cups'),
		('Tbsp', 'tablespoons'),
	)
	
	
	food = models.CharField(unique=True, max_length=100)
	calories = models.FloatField(validators=[MinValueValidator(.1)])
	carbs = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
	fat = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
	protein = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
	sodium = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
	sugar = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0)])
	serving_size = models.FloatField(default=1, validators=[MinValueValidator(.1)])
	units = models.CharField(max_length=100)
	
FoodDb = FoodDatabase(models.Model)
	
class FoodDatabaseForm(ModelForm):
	

	class Meta:
		model = FoodDatabase
		fields = ['food', 'calories', 'carbs', 'fat', 'protein', 'sodium', 'sugar',
					'serving_size', 'units']
		help_texts = {
			'sodium': 'If added, must be in milligrams.'}			
		for food in ['carbs', 'fat', 'protein', 'sugar']:
			help_texts[food] = 'If added, must be in grams.'
		
	
class UserMeals(models.Model):

	MEALS = (
		('B', 'Breakfast'),
		('L', 'Lunch'),
		('D', 'Dinner'), 
		('S', 'Snacks'),
	)
	
	UNITS = (
		('grams', 'grams'),
		('ounces', 'ounces'),
		('cups', 'cups'),
		('Tbsp', 'tablespoons'),
	)
	
	user = models.ForeignKey(User)
	date = models.DateField()
	meal_type = models.CharField(max_length=100, choices=MEALS)
	food_item = models.ForeignKey(FoodDatabase)
	portion = models.FloatField(default=0)
	units_consumed = models.FloatField(default=0)
	units = models.CharField(max_length=100)
	cal_eaten = models.FloatField(default=0)
	carbs = models.FloatField(default=0)
	fat = models.FloatField(default=0)
	protein = models.FloatField(default=0)
	sodium = models.FloatField(default=0)
	sugar = models.FloatField(default=0)
	

	
UserMealsDb = UserMeals(models.Model)

class RememberMeals(models.Model):
	
	MEALS = (
		('B', 'Breakfast'),
		('L', 'Lunch'),
		('D', 'Dinner'), 
		('S', 'Snacks'),
	)
	
	UNITS = (
		('grams', 'grams'),
		('ounces', 'ounces'),
		('cups', 'cups'),
		('Tbsp', 'tablespoons'),
	)
	title = models.CharField(unique=False, max_length=100)
	user = models.ForeignKey(User)
	date = models.DateField()
	meal_type = models.CharField(max_length=100, choices=MEALS)
	food_item = models.ForeignKey(FoodDatabase, default=0)
	portion = models.FloatField(default=0)
	units_consumed = models.FloatField(default=0)
	units = models.CharField(max_length=100)
	cal_eaten = models.FloatField(default=0)
	carbs = models.FloatField(default=0)
	fat = models.FloatField(default=0)
	protein = models.FloatField(default=0)
	sodium = models.FloatField(default=0)
	sugar = models.FloatField(default=0)
	

class UserDays(models.Model):

	user = models.ForeignKey(User)
	date = models.DateField()
	done = models.BooleanField(default=False)
	

		
	
	

	
	
	

