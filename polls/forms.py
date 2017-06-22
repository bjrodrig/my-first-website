from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, ButtonHolder, HTML
from crispy_forms.bootstrap import TabHolder, Tab
from django.forms.formsets import BaseFormSet
from django.core.validators import MinValueValidator

from polls import views
from .models import RememberMeals

html_personal_form = 0


class SignUpForm(UserCreationForm):
	first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
	last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
	email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
	
	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )
		
MEALS = (
		('B', 'Breakfast'),
		('L', 'Lunch'),
		('D', 'Dinner'), 
		('S', 'Snacks'),
	)	

class UserMealsForm(forms.Form):
	
	MEALS = (
		('B', 'Breakfast'),
		('L', 'Lunch'),
		('D', 'Dinner'), 
		('S', 'Snacks'),
	)

	
	servings = forms.FloatField(validators=[MinValueValidator(.01, message='Minimum allowed serving is .01.')])
	#serve_size = forms.CharField(choices=STANDARD_SERVINGS)
	meals = forms.ChoiceField(label="Add to", choices=MEALS)
	
class QuickAddForm(forms.Form):

	servings = forms.FloatField(label="Calories: ", validators=[MinValueValidator(.01)])
	meals = forms.ChoiceField(label="Meal Name: ", choices=MEALS)
	
	def __init__(self, *args, **kwargs):
		super(QuickAddForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper(self)
		self.helper.form_tag = False
		self.helper.disable_csrf = True
		
class PersonalMealsForm(forms.Form):
	
	
	food_selected = forms.BooleanField(
		required=False,
		label="",
	)
	food_quant = forms.FloatField(
		label="Qty",
		widget = forms.TextInput(attrs={'size':'2', 'maxlength':'5'}),
		validators=[MinValueValidator(.1)],
		
	)
	
	formset_index = forms.IntegerField(widget=forms.HiddenInput())
	#serve_size = forms.ChoiceField()
	today = forms.DateField(widget=forms.HiddenInput())
	meal = forms.CharField(widget=forms.HiddenInput())
	
	def __init__(self, *args, **kwargs):
		add_food_choices = kwargs.pop('add_food')
		today = kwargs.pop('today')
		meal = kwargs.pop('meal')
		super(PersonalMealsForm, self).__init__(*args, **kwargs)
		self.fields['serve_size'] = forms.ChoiceField(choices=add_food_choices)
		self.fields['today'].initial = today
		self.fields['meal'].initial = meal
	
	def set_index(self, index):
		self.fields['formset_index'].initial = index
		return index
	
	
	
	
class MultipleMealsForm(forms.Form):
	
	username = forms.HiddenInput()
	
class BaseMealFormSet(BaseFormSet):

	def __init__(self, *args, **kwargs):
		super(BaseMealFormSet, self).__init__(*args, **kwargs)
		#self.fields['serve_size_1'].choices = add_food_choices

	def add_fields(self, form, index):
		super(BaseMealFormSet, self).add_fields(form, index)
		form.set_index(index)
		
	def get_form_kwargs(self, index):
		kwargs = super(BaseMealFormSet, self).get_form_kwargs(index)
		kwargs['add_food'] = kwargs['add_food'][index]
		return kwargs

class SearchSavedMealsForm(forms.Form):

	title_to_search = forms.CharField(max_length=30, label="", required=False)
	
class SearchMealForm(forms.Form):

	food = forms.CharField(max_length=30, label="", required=False)
	
class RememberMealsForm(forms.Form):

	title = forms.CharField(max_length=100)
	
	def __init__(self, *args, **kwargs):
		self.request = kwargs.pop("request")
		super(RememberMealsForm, self).__init__(*args, **kwargs)
	
	def clean_title(self):
		data = self.cleaned_data['title']
		all_meals = RememberMeals.objects.filter(user=self.request.user)
		for item in all_meals:
			if data == item.title:
				raise forms.ValidationError("Cannot use title already in use")
		return data
	
	
