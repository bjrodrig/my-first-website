import datetime
import time


def five_weeks_from_now():
	today = datetime.date.today()
	five_weeks = today + datetime.timedelta(days=35)
	five_weeks = five_weeks.strftime("%B %d, %Y")
	print("five weeks: ", five_weeks)
	
five_weeks_from_now()


def calculate_portions(servings, form_units, amount_consumed, 
						selected, database_units):
	#database_units = selected.units
	database_serving_size = selected.serving_size
	#database_calories = selected.calories
	#if database_units.endswith('s'):
		#database_units = database_units.rstrip("s")
	#if form_units.endswith("s"):
		#form_units = form_units.rstrip("s")
	serving_conversions = {
		'gram': servings * 28.35,
		'ounce': servings / 28.35,
		'cup': servings / 16,
		'Tbsp': servings * 16,
		}
	if form_units == database_units:
		servings = servings * 1
	else:
		servings = serving_conversions.get(database_units)
	portion = ((servings * amount_consumed) / 
	                    (database_serving_size))
	return portion