import datetime
import time

from tabination.views import TabView
from django.shortcuts import get_object_or_404, render, redirect, render_to_response
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic
from django.template import loader
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, FloatField
from django.forms import formset_factory


from polls.forms import SignUpForm, UserMealsForm, QuickAddForm, PersonalMealsForm, MultipleMealsForm, BaseMealFormSet
from polls.forms import SearchSavedMealsForm, SearchMealForm, RememberMealsForm

from .models import UserProfile, UserProfileForm, FoodDatabase, FoodDatabaseForm, UserMeals, UserDays
from .models import RememberMeals

QuickAddFormSet = formset_factory(QuickAddForm)

net_calories = 0
change_per_week = 0
five_week_projection = 0
gain_or_lose = 0
gain_or_loss = 0
breakfast = lunch = dinner = snacks = meals = meal_names = query_sums = 0
query_totals = meal_name = 0
project_weight = 0
warning = False
quicktools_var = False
old_meal_name = None
old_today = None
done = False
copy_dates = []
quick_tools_list = []
quick_selected = ""
copy_date = ""
meal_to_initials = {
	'Breakfast': 'B',
	'Lunch': 'L',
	'Dinner': 'D',
	'Snacks': 'S'
	}
add_food_choices = ()
weight = ['gm', 'ounce', 'gram', 'oz']
volume = ['cup', 'teaspoon', 'tablespoon', 'fl oz', 'fluid ounce',
	          'tsp', 'tbsp']
simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
categories = ['cal_eaten', 'carbs', 'fat', 'protein', 'sodium', 'sugar']


def index(request):
	return render(request, 'polls/home.html')
	
def signup(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			login(request, user)
			return HttpResponseRedirect(reverse('polls:user_profile'))
	else:
		form = SignUpForm()
	return render(request, 'polls/signup.html', {'form': form})
		
#profile and initial goals set up section

@login_required(login_url='/polls/login/?next=/polls/')
def initial_goals(request, profile):
	global net_calories
	return render(request, 'polls/initial_goals.html', {'profile': profile, 'net_calories': net_calories,
	})

@login_required(login_url='/polls/login/?next=/polls/')
def user_profile(request):
	if request.method == 'POST':
		form = UserProfileForm(request.POST)
		if form.is_valid():
			profile = form.save(commit=False)
			profile.country = 'None Specified'
			profile.user = request.user
			profile.net_calories = calculate_net_calories(profile)
			get_nutrient_goals(profile)
			profile = form.save()
			context = {'profile': profile, 'change_per_week': abs(change_per_week),
			'five_week_proj': abs(five_week_projection), 'gain_or_lose': gain_or_lose,
			'gain_or_loss': gain_or_loss, 'five_weeks': five_weeks}
			return render_to_response('polls/initial_goals.html', context)
	else:
		form = UserProfileForm()
	
	return render(request, 'polls/user_profile.html', {'form': form})


#Requests Dealing with Food Diary: Retrieve, Add Food, Search Food, Delete Entries from diary,
#complete today's entry, make additional entries, go to yesterday diary, go to tomorrow diary

@login_required(login_url='/polls/login/')
def food(request):
	today = datetime.date.today()
	user = request.user
	create_user_days_record(user, today)
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
@login_required(login_url='/polls/login/?next=/polls/')
def update_food_diary(request, today):
	nutrition = ['carbs', 'fat', 'protein', 'sodium', 'sugar']
	user = request.user
	query_database_records(today, user)
	user_profile = query_daily_goals(user)
	subtract = get_remaining(query_totals, user_profile)
	project_weight = projected_weight(user, today)
	real_today = str(datetime.date.today())
	user_date_combo = UserDays.objects.get(user=user, date=today)
	foods_context = {'today': today, 'meals': meals, 'meal_names': meal_names, 
	          'query_sums': query_sums, 'query_totals': query_totals,
			  'user_profile': user_profile, 'subtract': subtract, 
			  'user_date_combo': user_date_combo, 'project_weight': project_weight, 
			  'warning': warning, 'meal_name': meal_name, 'quicktools_var': quicktools_var,
			  'real_today': real_today, 'copy_dates': copy_dates, 'copy_date': copy_date,
			  'quick_tools_list': quick_tools_list, 'quick_selected': quick_selected}
	return render(request, 'polls/food.html', foods_context)

	
@login_required(login_url='/polls/login/')
def add_food(request, today, name):
	global meals_for_form, form_units, amount_consumed
	get_meals_2 = []
	meals_for_form = meal_to_initials.get(name)
	all_records = UserMeals.objects.all
	user = request.user
	recent_query = query_recent_meals(user)
	count_recent = len(recent_query)
	frequent_query = query_frequent_meals(user)
	total_query = recent_query + frequent_query
	count_frequent = len(total_query)
	get_meals = RememberMeals.objects.filter(user=user)
	get_meals_2 = remove_duplicates_remember(get_meals, get_meals_2)
	add_food_choices = create_add_food_choices(total_query, user)
	add_food_choices = list(add_food_choices)
	add_food_names = food_names(total_query)
	for q in get_meals_2:
		add_food_names.append(q.title)
	count_user_meals = len(add_food_names)
	#print("count user meals: ", count_user_meals)
	quant_int = [{'food_quant': q.portion} for q in total_query]
	for q in get_meals_2:
		quant_int.append({'food_quant': 1})
	recent_int = quant_int 
	MealFormSet = formset_factory(PersonalMealsForm, formset=BaseMealFormSet, extra=0)
	if request.method == "POST":
		meal_formset = MealFormSet(request.POST, form_kwargs={'add_food': add_food_choices, 'today': today,
		                                        'meal': name}, initial=recent_int)
		mult_form = MultipleMealsForm(request.POST)
		print(meal_formset.errors)
		if mult_form.is_valid() and meal_formset.is_valid():
			username = mult_form.cleaned_data.get("username")
			
			for meal_form in meal_formset:
				form_index = meal_form.cleaned_data.get('formset_index')
				meal_checked = meal_form.cleaned_data.get('food_selected')
				if meal_checked:
					user = request.user
					servings = meal_form.cleaned_data.get('food_quant')
					meal = meal_form.cleaned_data.get('meal')
					meal = meal_to_initials.get(meal)
					serve_size = meal_form.cleaned_data.get('serve_size')
					today = meal_form.cleaned_data.get('today')
					#print("count frequent: ", count_frequent)
					#print("form index: ", form_index)
					if form_index >= count_frequent:
						title = add_food_names[form_index]
						get_meal_2 = RememberMeals.objects.filter(user=user, title=title)
						for q in get_meal_2:
							selected = q.food_item
							amount_consumed = q.units_consumed
							form_units = q.units
							portion = servings * q.portion
							create_database_record(selected, amount_consumed, form_units, 
			                       meal, portion, today, user, servings)
					else:
						selected = total_query[form_index].food_item
						get_units_amount(serve_size)
						database_units = selected.units.lower().strip().rstrip("s")
						#print("database_units: ", database_units)
						portion = calculate_portions(servings, form_units, amount_consumed, 
			                             selected, database_units, simple_volume)
						create_database_record(selected, amount_consumed, form_units, 
			                       meal, portion, today, user, servings)
			return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	else:
		meal_formset = MealFormSet(form_kwargs={'add_food': add_food_choices, 'today': today,
		                                        'meal': name}, initial=recent_int)
		
		mult_form = MultipleMealsForm()
	search_form = SearchMealForm()
	context = {'meal_formset': meal_formset, 'add_food_names': add_food_names, 
			   'mult_form': mult_form, 'today': today,'count_recent': count_recent,
			   'count_frequent': count_frequent, 'count_user_meals': count_user_meals,
			   'search_form': search_form}
	return render(request, 'polls/add_food.html', context)
	
@login_required(login_url='/polls/login/')
def search_food(request, food, today):
	global quicktools_var
	quicktools_var = False
	all_foods = FoodDatabase.objects.all()
	try:
		selected = FoodDatabase.objects.get(food=food)
	except FoodDatabase.DoesNotExist:
		selected = 5
	meals = ['Breakfast', 'Lunch', 'Dinner', 'Snack']
	database_units = get_database_units(selected)
	if selected == 5:
		selected = ""
	weight = ['gm', 'ounce', 'gram', 'oz']
	volume = ['cup', 'teaspoon', 'tablespoon', 'fl oz', 'fluid ounce',
	          'tsp', 'tbsp']
	simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
	if request.method == "POST":
		form = UserMealsForm(request.POST)
		if form.is_valid():
			servings = form.cleaned_data.get('servings')
			meal = form.cleaned_data.get('meals')
			serve_size = request.POST.get('serve_size')
			serve_size = serve_size.split(' ')
			amount_consumed = float(serve_size.pop(0))
			if len(serve_size) > 1:
				serve_size = " ".join(serve_size)
			else:
				serve_size = str(serve_size[0])
			form_units = serve_size.lower().strip().rstrip("s")
			#if form_units == 'fluid':
			#	form_units = 'fluid ounce'
			
			selected = FoodDatabase.objects.get(food=food)
			today = request.POST.get('today')
			today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
			portion = calculate_portions(servings, form_units, amount_consumed, 
			                             selected, database_units, simple_volume)
			#print("portion: ", portion)
			user = request.user
			create_database_record(selected, amount_consumed, form_units, 
			                       meal, portion, today, user, servings)
			return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	else:
		form = UserMealsForm(initial={'meals': meals_for_form})
	context = {'all_foods': all_foods, 'selected': selected, 'meals': meals,
	           'database_units': database_units, 'weight': weight, 
			   'volume': volume, 'simple_volume': simple_volume, 'today': today,
			   'form': form,}
	return render(request, 'polls/search_food.html', context)
	
def delete_user_meal(request, today, q):
	id = q
	food_obj = UserMeals.objects.filter(id=id).delete()
	reset_quicktools()
	#return render(request, 'polls/home.html')
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def completed_entry(request, today):
	global done, user_date_combo
	user = request.user
	user_date_combo = get_done_status(user, today, True)
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def make_additional_entries(request, today):
	global done, user_date_combo
	user = request.user
	user_date_combo = get_done_status(user, today, False)
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def yesterday_food(request, today):
	today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
	today = today - datetime.timedelta(days=1)
	user = request.user
	create_user_days_record(user, today)
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def tomorrow_food(request, today):
	today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
	today = today + datetime.timedelta(days=1)
	user = request.user
	create_user_days_record(user, today)
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
#Retrieve and delete remembered meals

@login_required(login_url='/polls/login/')
def my_meals(request, title):
	user = request.user
	today = datetime.date.today()
	get_meal = RememberMeals.objects.filter(user=user)
	specific_meal = []
	query_sums = []
	get_meal_2 = []
	if title != "None":
		specific_meal = RememberMeals.objects.filter(user=user, title=title)
		for c in categories:
			get_sum = specific_meal.aggregate(Sum(c))
			a = c + "__sum"
			query_sums.append(get_sum.get(a))
	if request.method == 'POST':
		form = SearchSavedMealsForm(request.POST)
		if form.is_valid():
			search_criteria = form.cleaned_data.get('title_to_search')
			if search_criteria:
				get_meal = RememberMeals.objects.filter(user=user, title__icontains=search_criteria)
			else:
				get_meal = RememberMeals.objects.filter(user=user)
	else:
		form = SearchSavedMealsForm()
	get_meal_2 = remove_duplicates_remember(get_meal, get_meal_2)
	context = {'form': form, 'user': user, 'get_meal': get_meal, 'specific_meal': specific_meal,
	           'query_sums': query_sums, 'title': title, 'categories': categories,
			   'get_meal_2': get_meal_2}
	return render(request, 'polls/my_meals.html', context)
	
def my_meals_delete(request, title):
	user = request.user
	RememberMeals.objects.filter(user=user, title=title).delete()
	title = "None"
	return HttpResponseRedirect(reverse('polls:my_meals', args=(title,)))
	
# QuickTools
	
def quick_tools_open(request, today, name):
	global quicktools_var, meal_name, old_meal_name, old_today, quick_tools_list
	meal_name = name
	quicktools_var = True
	quick_tools_list = ['Quick add calories', 'Copy yesterday', 'Copy to today', 
	                    'Copy from date', 'Copy to date', 'Remember Meal']
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def quicktools_options(request, today, name, q):
	global quick_selected
	quicktools_dict = {
		'Quick add calories': "",
		'Copy yesterday': copy_from_or_to_date,
		'Copy to today': copy_from_or_to_date,
		'Copy from date': copy_from_or_to_date,
		'Copy to date': copy_from_or_to_date,
		'Remember Meal': remember_meal_func,
	}
	run_func = quicktools_dict.get(q)
	user = request.user
	quick_selected = q
	if run_func == copy_from_or_to_date:
		run_func(user, today, name)
		return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	elif run_func == remember_meal_func:
		return HttpResponseRedirect(reverse('polls:remember_meal_func', args=(today, name)))
	else:
		return HttpResponseRedirect(reverse('polls:quick_add_calories', args=(today, name)))
		
def remember_meal_func(request, name, today):
	global query_sums, meals
	user = request.user
	date_today = datetime.datetime.strptime(today, "%Y-%m-%d").date()
	meal_name = meal_to_initials.get(name)
	query_database_records(today, user)
	query_sums_specific = {
		'B': 0,
		'L': 1,
		'D': 2,
		'S': 3
	}
	get_sum = query_sums_specific.get(meal_name)
	query_sums = query_sums[get_sum]
	meals = meals[get_sum]
	if request.method == "POST":
		form = RememberMealsForm(request.POST, request=request)
		if form.is_valid():
			title = form.cleaned_data['title']
			for q in meals:
				RememberMeals.objects.create(title=title, user=user, date=q.date, meal_type=q.meal_type,
		                                     food_item=q.food_item, portion=q.portion, units_consumed=q.units_consumed,
											 units=q.units, cal_eaten=q.cal_eaten, carbs=q.carbs, fat=q.fat,
											 protein=q.protein, sodium=q.sodium, sugar=q.sugar)
			reset_quicktools()
			return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	else:
		form = RememberMealsForm(request=request)
	context = {'today': today, 'form': form, 'query_sums': query_sums, 'meals': meals}
	return render(request, 'polls/remember_meal.html', context)
	
def quick_add_calories(request, today, name):
	meals_for_form = meal_to_initials.get(name)
	if request.method == "POST":
		form = QuickAddForm(request.POST)
		if form.is_valid():
			user = request.user
			servings = form.cleaned_data.get('servings')
			meal = form.cleaned_data.get('meals')
			#today = request.POST.get('today')
			today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
			form_units = "serving"
			amount_consumed = 1
			select_food = FoodDatabase.objects.get(food="Quick Add")
			database_units = "serving"
			portion = calculate_portions(servings, form_units, amount_consumed, 
			                             select_food, database_units, simple_volume)
			create_database_record(select_food, amount_consumed, form_units, 
			                       meal, portion, today, user, servings)
			reset_quicktools()
			return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	else:
		form = QuickAddForm(initial={'meals': meals_for_form})
	context = {'today': today, 'form': form,}
	return render(request, 'polls/quick_add_cal.html', context)
	
def get_record_to_copy(request, today, name, c):
	global copy_dates, copy_date, quicktools_var
	user = request.user
	name = meal_to_initials.get(name)
	copy_dates = []
	copy_date = c
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	
def copy_to_today(request, today, name, m, c):
	global quicktools_var
	quicktools_var = False
	#real_today = datetime.date.today()
	user = request.user
	name = meal_to_initials.get(name)
	m = meal_to_initials.get(m)
	if quick_selected == "Copy from date" or quick_selected == "Copy yesterday":
		copy_dates_quicktools(user, m, c, today, name)
	elif quick_selected == "Copy to date" or quick_selected == "Copy to today":
		copy_dates_quicktools(user, name, today, c, m)
	#return(request, "polls/home.html")
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))	
	
def quick_tools_close(request, today, name):
	global meal_name, old_meal_name, old_today
	meal_name = name
	reset_quicktools()
	return HttpResponseRedirect(reverse('polls:update_food_diary', args=(today,)))
	

# Add Food to Database

def add_food_to_database(request):
	if request.method == 'POST':
		form = FoodDatabaseForm(request.POST)
		if form.is_valid():
			form.save()
			return render(request, 'polls/success.html')
	else:
		form = FoodDatabaseForm()
	return render(request, 'polls/add_food_to_database.html', {'form': form})
	



# Non Request Functions

	
def copy_from_or_to_date(user, today, name):
	global copy_dates
	today = datetime.datetime.strptime(today, '%Y-%m-%d').date()
	copy_dates = []
	if quick_selected == "Copy from date":
		start = range(1, 8, 1)
	elif quick_selected == "Copy to date":
		start = range(-3, 4, 1)
	else:
		start = range(1, 2, 1)
	for i in start:
		date = today - datetime.timedelta(days=i)
		real_today = datetime.date.today()
		if quick_selected == "Copy to today":
			date = real_today
		elif quick_selected == "Copy yesterday":
			date = real_today - datetime.timedelta(days=1)
		copy_dates.append(date)
	

def copy_dates_quicktools(user, name, date_copy_from, date_copy_to, meal_copy_to):
	#print("date copy from: ", date_copy_from)
	#print("date copy to: ", date_copy_to)
	if UserMeals.objects.filter(user=user, date=date_copy_from, meal_type=name).exists():
		queryset = UserMeals.objects.filter(user__exact=user, 
									date__exact=date_copy_from, meal_type__exact=name)
		for q in queryset:
			create_record = UserMeals(user=user, date=date_copy_to, meal_type=meal_copy_to, 
								  food_item=q.food_item, portion=q.portion, 
								  units_consumed=q.units_consumed, units=q.units,
								  cal_eaten=q.cal_eaten, carbs=q.carbs, fat=q.fat,
								  protein=q.protein, sodium=q.sodium, sugar=q.sugar)
			create_record.save()
	reset_quicktools()
	
	
def reset_quicktools():
	global quicktools_var, copy_dates, quick_selected
	quicktools_var = False
	copy_dates = []
	quick_selected = ""


def calculate_BMR(profile):
	weight_in_kg = profile.weight / 2.2
	height_in_cm = (profile.height_ft * 12 + profile.height_in) * 2.54
	age = datetime.date.today() - profile.birth_date
	age = age.total_seconds()/(60 * 60 * 24 * 365)
	
	if profile.gender == 'M':
		BMR = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age + 5
	else:
		BMR = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age - 161
	
	lifestyle = {
				'S': 1.2,
				'LA': 1.375,
				'A': 1.55,
				'VA': 1.725,
				}
	BMR = BMR * lifestyle.get(profile.lifestyle)
	return BMR
	
def gain_or_loss_weight(change_per_week):
	global gain_or_lose
	global gain_or_loss
	if change_per_week > 0:
		gain_or_loss = "gain"
		gain_or_lose = "gain"
	else:
		gain_or_loss = "loss"
		gain_or_lose = "lose"
		
def five_weeks_from_now():
	today = datetime.date.today()
	five_weeks = today + datetime.timedelta(days=35)
	five_weeks = five_weeks.strftime("%B %d, %Y")
	return five_weeks
	
def calculate_net_calories(profile):
	global change_per_week
	global five_week_projection
	global five_weeks
	BMR = calculate_BMR(profile)
	goal = {
				'L2': -1000,
				'L1.5': -750,
				'L1': -500,
				'M': 0,
				'G.5': 250,
				'G1': 500,
			}
	net_calories = BMR + goal.get(profile.goal)
	if profile.gender == 'M':
		net_calories = max(net_calories, 1500)
	else:
		net_calories = max(net_calories, 1200)
	change_per_week = round((net_calories - BMR) * 7 / 3500, 2)
	five_week_projection = 5 * change_per_week
	gain_or_loss_weight(change_per_week)
	five_weeks = five_weeks_from_now()
	return round(net_calories, 0)
	
def get_database_units(selected):
	try:
		database_units_1 = selected.units.lower().strip().rstrip("s")
	except:
		database_units = 0
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
	
	
def calculate_volume_servings(volume_conv, amount_consumed, form_units,
                              database_units):
	conv = [form_units, form_units]
	while conv[1] != database_units:
		conv = volume_conv.get(conv[1])
		amount_consumed = amount_consumed * conv[0]
		#print("amount_consumed", amount_consumed)
		#conv = volume_conv.get(conv[1])
	return amount_consumed
		
		
	
def volume_conversions(amount_consumed, form_units, database_units):
	order = ['tsp', 'tbsp', 'fluid ounce', 'cup']
	volume_conv = {
		'tsp': [(1/3), 'tbsp'],
		'tbsp': [.5, 'fluid ounce'],
		'fluid ounce': [(1/8), 'cup'],
	}
	volume_conv_v2 = {
		'cup': [8, 'fluid ounce'],
		'fluid ounce': [2, 'tbsp'],
		'tbsp': [3, 'tsp'],
	}
	start = order.index(form_units)
	end = order.index(database_units)
	if start < end:
		volume_conv = volume_conv
	else:
		volume_conv = volume_conv_v2
	amount_consumed = calculate_volume_servings(volume_conv, amount_consumed, form_units,
		                      database_units)
	return amount_consumed
	
def calculate_portions(servings, form_units, amount_consumed, 
						selected, database_units, simple_volume):
	database_serving_size = selected.serving_size
	variations = {
		'gram': 'gm',
		'ounce': 'oz',
		'tbsp': 'tablespoon',
		'tsp': 'teaspoon',
		'fluid ounce': 'fl oz',
		'gm': 'gram',
		'oz': 'ounce',
		'tablespoon': 'tbsp',
		'teaspoon': 'tsp',
		'fl oz': 'fluid ounce',
		
	}
	# check if database units and form units are essentially the same
	if form_units == database_units:
		amount_consumed = amount_consumed * 1
	else:
		try:
			variation = variations.get(form_units) 
		except:
			pass
		else:
			if variation == database_units:
				amount_consumed = amount_consumed * 1
				database_units = form_units
	# if weight, convert form units to database units
	if form_units != database_units:
		if database_units == 'ounce' or database_units == 'oz':
			amount_consumed = amount_consumed / 28.35
		elif database_units == 'gram' or database_units == 'gm':
			amount_consumed = amount_consumed * 28.35
	if database_units in simple_volume:
		amount_consumed = volume_conversions(amount_consumed, form_units, database_units)
	portion = ((servings * amount_consumed) / 
	                    (database_serving_size))
	return portion
	
def create_database_record(selected, amount_consumed, form_units, 
							meal, portion, today, user, servings):
	units_consumed = servings * amount_consumed
	selected_fields = [selected.calories, selected.carbs, selected.fat,
	                   selected.protein, selected.sodium, selected.sugar]
	user_quant = []
	for field in selected_fields:
		try:
			user_quant.append(portion * field)
		except:
			user_quant.append(0)
	get_meals = UserMeals(date=today, meal_type=meal, portion=portion, 
	                units_consumed=units_consumed, units=form_units, 
					food_item=selected, user=user, cal_eaten=user_quant[0],
					carbs=user_quant[1], fat=user_quant[2], protein=user_quant[3],
					sodium=user_quant[4], sugar=user_quant[5])
	get_meals.save()
	
def convert_query_sums(sum_info, title):
	a = title + "__sum"
	get_sum = sum_info.get(a)
	#print("get_sum: ", get_sum)
	if get_sum != None:
		a = get_sum
	else:
		a = " "
	return a
	
def get_query_totals(user, today):
	categories = ['cal_eaten', 'carbs', 'fat', 'protein', 'sodium', 'sugar']
	query_totals = []
	for title in categories:
		a = UserMeals.objects.filter(user__exact=user, 
									date__exact=today).aggregate(Sum(title))
		a = convert_query_sums(a, title)
		query_totals.append(a)
	return query_totals
	
def sum_of_calories_and_more(meal_codes, categories, today, user):
	global query_sums, query_totals
	query_sums_b = []
	query_sums_l = []
	query_sums_d = []
	query_sums_s = []
	query_sum_dict = {
		'B': query_sums_b,
		'L': query_sums_l,
		'D': query_sums_d,
		'S': query_sums_s,
	}
	for meal in meal_codes:
		query_sums = query_sum_dict.get(meal)
		for title in categories:
			sum_info = UserMeals.objects.filter(user__exact=user, date__exact=today,
			                                    meal_type__exact=meal).aggregate(Sum(title))
			a = convert_query_sums(sum_info, title)
			query_sums.append(a)
	query_sums = [query_sums_b, query_sums_l, query_sums_d, query_sums_s]
	query_totals = get_query_totals(user, today)
	
	
	
def query_database_records(today, user):
	global done
	global breakfast, lunch, dinner, snacks, meals, meal_names
	#done = False
	queryset = UserMeals.objects.filter(user__exact=user, date__exact=today)
	breakfast = []
	lunch = []
	dinner = []
	snacks = []
	for q in queryset:
		if q.meal_type == 'B':
			breakfast.append(q)
		elif q.meal_type == 'L':
			lunch.append(q)
		elif q.meal_type == 'D':
			dinner.append(q)
		else:
			snacks.append(q)
	meals = [breakfast, lunch, dinner, snacks]
	meal_names = ['Breakfast', 'Lunch', 'Dinner', 'Snacks']
	i = 0
	meal_codes = ['B', 'L', 'D', 'S']
	categories = ['cal_eaten', 'carbs', 'fat', 'protein', 'sodium', 'sugar']
	sum_of_calories_and_more(meal_codes, categories, today, user)
	
def query_daily_goals(user):
	goals = UserProfile.objects.get(user__exact=user)
	user_profile = [goals.net_calories, goals.carbs, goals.fat,
					goals.protein, goals.sodium, goals.sugar]
	return user_profile
	
def get_nutrient_goals(profile):
	profile.carbs = profile.net_calories / 8
	profile.fat = profile.net_calories / 30
	profile.protein = profile.net_calories / 20
	profile.sodium = 2300
	profile.sugar = 45
		
	
def get_remaining(query_totals, user_profile):
	count = 0
	subtractions = []
	for q in query_totals:
		try:
			float(q)
		except:
			q = 0
		subtract = user_profile[count] - float(q)
		subtractions.append(subtract)
		count = count + 1
	return subtractions
	
def projected_weight(user, today):
	global warning
	profile = UserProfile.objects.get(user__exact=user)
	BMR = calculate_BMR(profile)
	query_totals = get_query_totals(user, today)
	try:
		float(query_totals[0])
	except:
		query_totals[0] = 0
	if profile.gender == 'M':
		too_low = 1200
	else:
		too_low = 1000
	if query_totals[0] < too_low:
		warning = True
	else:
		warning = False
	weight_change = (float(query_totals[0]) - BMR) / 100
	#weight_change = cal_change/3500
	project_weight = profile.weight + weight_change
	return project_weight
	
def get_done_status(user, today, done):
	user_date_combo = UserDays.objects.get(user=user, date=today)
	user_date_combo.done = done
	user_date_combo.save()
	return user_date_combo
	
def create_user_days_record(user, today):
	#UserDays.objects.all().delete()
	if UserDays.objects.filter(user=user, date=today).exists():
		pass
	else:
		create_user_days = UserDays(date=today, user=user, done=False)
		create_user_days.save()
		
def query_recent_meals(user):
	queryset = UserMeals.objects.filter(user__exact=user).order_by('-date')
	food_items = []
	recent_query = []
	for q in queryset:
		if q.food_item.food != "Quick Add":
			if q.food_item not in food_items:
				food_items.append(q.food_item)
				recent_query.append(q)
	try:
		recent_query = recent_query[:5]
	except:
		pass
	return recent_query
	
def query_frequent_meals(user):
	quick = FoodDatabase.objects.filter(food="Quick Add").values_list('id', flat=True)
	#print(quick)
	excl = UserMeals.objects.filter(user=user).exclude(food_item=quick)
	queryset = excl.values('food_item').annotate(c=Count('food_item')).order_by('-c')[:5]
	food_database_query = []		   
	for q in queryset:
		food_item_id = q.get('food_item')
		a = FoodDatabase.objects.get(id=food_item_id)
		food_database_query.append(a)
	# query user meals - order by most recent
	new_queryset = UserMeals.objects.filter(user__exact=user).order_by('-date')
	# going backwards-if food item matches food item in recent-append to new list
	frequent_query = []
	for f in food_database_query:
		for n in new_queryset:
			if f == n.food_item:
				if not frequent_query:
					frequent_query.append(n)
				else:
					for q in frequent_query:
						if q.food_item.food == n.food_item.food:
							break
						elif frequent_query.index(q) == (len(frequent_query) - 1):
							frequent_query.append(n)
	return frequent_query
	
	
def create_add_food_choices(recent_query, user):
	weight = ['gm', 'ounce', 'gram', 'oz']
	volume = ['cup', 'teaspoon', 'tablespoon', 'fl oz', 'fluid ounce',
	          'tsp', 'tbsp']
	simple_volume = ['cup', 'tbsp', 'tsp', 'fluid ounce']
	choices = []
	for n in range(0, len(recent_query), 1):
		
		each_list = []
		# consider changing first serving_size to a standard amount from food database table instead
		serving_size = round(recent_query[n].units_consumed / recent_query[n].portion, 2)
		if serving_size != 1:
			units = str(recent_query[n].units) + "s"
		else:
			units = str(recent_query[n].units)
		first_choice = str(serving_size) + " " + units
		each_list.append((first_choice, first_choice))
		selected = recent_query[n]
		form_units = selected.units.lower().strip().rstrip("s")
		if (form_units == 'teaspoon' or form_units == 'tablespoon' or 
		    form_units == 'fl oz'):
			form_units = get_database_units(selected)
		if form_units in weight:
			if form_units != 'gram' and form_units != 'gm' or serving_size != 1:
				each_list.append(('1 gram', '1 gram'))
			if form_units != 'oz' and form_units != 'ounce' or serving_size != 1:
				each_list.append(('1 ounce', '1 oz'))
		elif form_units in simple_volume:
			for unit in simple_volume:
				if serving_size != 1 or form_units != unit:
					choice = "1 " + str(unit)
					each_list.append((choice, choice))
		each_list = tuple(each_list)
		#print("choices", choices)
		choices.append(each_list)
	get_meal = RememberMeals.objects.filter(user=user)
	get_meal_2 = []
	get_meal_2 = remove_duplicates_remember(get_meal, get_meal_2)
	for q in get_meal_2:
		each_list = []
		each_list.append(("1 Meal", "1 Meal"))
		each_list = tuple(each_list)
		choices.append(each_list)
	choices = tuple(choices)
	return choices
		
def food_names(recent_query):
	food_names = []
	for q in recent_query:
		food_names.append(q.food_item.food)
	return food_names
		
def get_units_amount(get_serve_size):
	global serve_size, form_units, amount_consumed
	serve_size = get_serve_size.split(' ')
	amount_consumed = float(serve_size.pop(0))
	if len(serve_size) > 1:
		serve_size = " ".join(serve_size)
	else:
		serve_size = str(serve_size[0])
	form_units = serve_size.lower().strip().rstrip("s")
	
	
def remove_duplicates_remember(get_meal, get_meal_2):
	for q in get_meal:
		if get_meal_2:
			for a in get_meal_2:
				if q.title == a.title:
					break
				elif get_meal_2.index(a) == (len(get_meal_2) - 1):
					get_meal_2.append(q)
						
		else:
			get_meal_2.append(q)
	return get_meal_2
	
	

# Create your views here.
