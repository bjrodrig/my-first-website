from django import template
register = template.Library()

@register.filter
def at_index(array, index):
	return array[index]

@register.filter	
def round1(value):
	return round(value, 1)
	
@register.filter
def subtract(value1, value2):
	return float(value1) - float(value2)
	
@register.filter
def make_int(value):
	return int(value)
	
@register.filter
def lookup(d, key):
	return d[key]
	
@register.filter
def add_one(value):
	return value + 1
	
@register.filter
def make_zero(value):
	return 0

