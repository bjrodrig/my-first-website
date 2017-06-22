from django.contrib import admin

from .models import UserProfile, FoodDatabase, RememberMeals, UserMeals
from django.contrib.auth.models import AnonymousUser, User

#class ChoiceInline(admin.TabularInline):
#	model = Choice
#	extra = 3

#class QuestionAdmin(admin.ModelAdmin):
#	fieldsets = [
#		(None, 			      {'fields': ['question_text']}),
#		('Date information',  {'fields': ['pub_date'], 'classes': ['collapse']}),
#	]
#	inlines = [ChoiceInline]
#	list_display = ('question_text', 'pub_date', 'was_published_recently')
#	list_filter = ['pub_date']
#	search_fields = ['question_text']

class UserMealsAdmin(admin.ModelAdmin):
	fields = ('units')
	list_display = ('units')
	
#admin.site.register(Question, QuestionAdmin)
admin.site.register(UserProfile)
admin.site.register(FoodDatabase)
admin.site.register(RememberMeals)
admin.site.register(UserMeals)


# Register your models here.
