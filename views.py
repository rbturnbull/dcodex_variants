from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from dcodex.util import get_request_dict
import logging



from .models import *

def index(request):
    return HttpResponse("Hello, world. You're at the DCodex Variants index.")
    

def location_for_witness( request, witness_slug, location_id ):
    location = get_object_or_404(LocationUBS, id=location_id) 

    witness = FamilyWitness.objects.filter( family__name=witness_slug ).first()
    if witness:
        manuscripts = witness.family.manuscripts_at( location.start_verse )
        attestation = witness.attestations_at( location ).first()
        text = attestation.text if attestation else ""
        return render(request, 'dcodex_variants/location_for_familywitness.html', {'location': location, 'witness':witness, 'manuscripts':manuscripts, 'text':text } )

    return HttpResponse(f"Cannot find witness: {witness_slug}")


def attestations( request ):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get('reading_id')
    location_id = request_dict.get('location_id')
    location = get_object_or_404(Location, id=location_id) 
    
    return HttpResponse(html)

def remove_attestation( request ):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get('reading_id')
    reading = get_object_or_404(Reading, id=reading_id) 

    witness_id = request_dict.get('witness_id')
    witness = get_object_or_404(WitnessBase, id=witness_id) 
    
    witness.remove_attestation( reading=reading )
    return HttpResponse("OK")


def set_attestation( request ):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get('reading_id')
    reading = get_object_or_404(Reading, id=reading_id) 

    witness_id = request_dict.get('witness_id')
    witness = get_object_or_404(WitnessBase, id=witness_id) 
    
    response = witness.set_attestation( reading=reading, text=request_dict.get('text') )
    return HttpResponse("OK" if response else "FAIL")
    

    
