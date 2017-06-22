from datetime import datetime
import time

def calculate_net_calories(weight, height_ft, height_in, birth_date, gender):
	weight_in_kg = weight/2.2
	height_in_cm = (height_ft * 12 + height_in) * 2.54
	today = datetime.today()
	print("today is: ", today)
	age = today - birth_date
	age = age.total_seconds()
	age = age/(60 * 60 * 24 * 365)
	
	print("age is: ", age)
	if gender == 'M':
		BMR = 66.47 + (13.75 * weight_in_kg) + (5.0 * height_in_cm) - (6.75 * age)
	else:
		BMR = 665.09 + (9.56 * weight_in_kg) + (1.84 * height_in_cm) - (4.67 * age)
	print("BMR is: ", BMR)
	
def mkdate(datestr):
	print(datetime.strptime(datestr, '%Y-%m-%d'))
	return datetime.strptime(datestr, '%Y-%m-%d')
	


mkdate('1991-10-01')	
calculate_net_calories(104, 4, 11, mkdate('1991-10-01'), 'F')


def calculate_net_calories(profile):
	weight_in_kg = profile.weight / 2.2
	height_in_cm = (profile.height_ft * 12 + profile.height_in) * 2.54
	today = datetime.date.today()
	#print("today: ", today)
	age = today - profile.birth_date
	#print("age is: ", age)
	age = age.total_seconds()
	age = age/(60 * 60 * 24 * 365)
	
	print("age is: ", age)
	if profile.gender == 'M':
		BMR = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age + 5
	else:
		BMR = 10 * weight_in_kg + 6.25 * height_in_cm - 5 * age - 161
	print("BMR is: ", BMR)
	lifestyle = {
				'S': BMR * 1.2,
				'LA': BMR * 1.375,
				'A': BMR * 1.55,
				'VA': BMR * 1.725,
				}
	BMR = lifestyle.get(profile.lifestyle)
	print("BMR 2 is: ", BMR)
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
	print("net calories is: ", net_calories)
	change_per_week = (BMR - net_calories) * 7 / 3500
	print("change per week: ", change_per_week)
	five_week_projection = 5 * change_per_week