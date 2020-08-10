from django import template
import logging

register = template.Library()

@register.simple_tag
def witness_attests_reading(witness, reading):
    return witness.attests_reading(reading)

@register.filter
def button_for_reading(witness, reading):
    return "btn-primary" if witness.attests_reading(reading) else "btn-outline-primary"    
