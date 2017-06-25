from django.conf.urls import url
from django.contrib.auth import views as auth_views
from . import views
from polls.views import SignUpWizard
from polls.forms import SignUpForm
from polls.models import UserProfileForm

app_name = 'polls'
urlpatterns = [

	#home
	url(r'^$', views.index, name='index'),
	
	#signup/login/logout
	#url(r'^signup/$', views.signup, name='signup'),
	url(r'^signup/$', SignUpWizard.as_view([SignUpForm, UserProfileForm]), name="signup"),
	url(r'^login/$', auth_views.login, name='login'),
	url(r'^logout/$', auth_views.logout, name='logout'),
	
	#initial profile setup
	url(r'^user_profile/$', views.user_profile, name='user_profile'),
	url(r'^(?P<profile>.*)/initial_goals/$', views.initial_goals, name='initial_goals'),
	
	#food diary
	url(r'^food/$', views.food, name='food'),
	url(r'^(?P<today>.*)/update_food_diary/$', views.update_food_diary, name='update_food_diary'),
	url(r'^(?P<today>.*)/(?P<name>.*)/add_food/$', views.add_food, name='add_food'),
	url(r'^(?P<food>.*)/(?P<today>.*)/search_food/$', views.search_food, name='search_food'),
	url(r'^(?P<today>.*)/(?P<q>.*)/delete_user_meal/$', views.delete_user_meal, name='delete_user_meal'),
	url(r'^(?P<today>.*)/completed_entry/$', views.completed_entry, name='completed_entry'),
	url(r'^(?P<today>.*)/make_additional_entries/$', views.make_additional_entries, name='make_additional_entries'),
	url(r'^(?P<today>.*)/yesterday_food/$', views.yesterday_food, name='yesterday_food'),
	url(r'^(?P<today>.*)/tomorrow_food/$', views.tomorrow_food, name='tomorrow_food'),
	
	#Retrieve and Delete remembered meals
	url(r'^(?P<title>.*)/my_meals/$', views.my_meals, name='my_meals'),
	url(r'^(?P<title>.*)/my_meals/$', views.my_meals, name='my_meals'),
	url(r'^(?P<title>.*)/my_meals_delete/$', views.my_meals_delete, name='my_meals_delete'),
	
	
	#QuickTools
	url(r'^(?P<today>.*)/(?P<name>.*)/quick_tools_open/$', views.quick_tools_open, name='quick_tools_open'),
	url(r'^(?P<today>.*)/(?P<name>.*)/(?P<q>.*)/quicktools_options/$', views.quicktools_options, name='quicktools_options'),
	url(r'^(?P<today>.*)/(?P<name>.*)/remember_meal_func/$', views.remember_meal_func, name='remember_meal_func'),
	url(r'^(?P<today>.*)/(?P<name>.*)/quick_add_calories/$', views.quick_add_calories, name='quick_add_calories'),
	url(r'^(?P<today>.*)/(?P<name>.*)/(?P<c>.*)/get_record_to_copy/$', views.get_record_to_copy, name='get_record_to_copy'),
	url(r'^(?P<today>.*)/(?P<name>.*)/(?P<m>.*)/(?P<c>.*)/copy_to_today/$', views.copy_to_today, name='copy_to_today'),
	url(r'^(?P<today>.*)/(?P<name>.*)/quick_tools_close/$', views.quick_tools_close, name='quick_tools_close'),
	
	#Add Food to Database
	url(r'^add_food_to_database/$', views.add_food_to_database, name='add_food_to_database'),
	
]