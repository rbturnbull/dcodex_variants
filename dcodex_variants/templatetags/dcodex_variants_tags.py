from django import template
import logging

from dcodex_variants.models import Attestation, Contra

register = template.Library()

@register.simple_tag
def witness_attests_reading(witness, reading):
    return witness.attests_reading(reading)

@register.filter
def button_for_reading(witness, reading):
    return "btn-primary" if witness.attests_reading(reading) else "btn-outline-primary"    

@register.simple_tag
def transcription_contra_class(witness, location, transcription):
    attestations = Attestation.objects.filter(witness=witness, reading__location=location)    
    contra = Contra.objects.filter( attestation__in=attestations, manuscript=transcription.manuscript, verse=transcription.verse ).first()
    return "btn-warning" if contra else ""    
