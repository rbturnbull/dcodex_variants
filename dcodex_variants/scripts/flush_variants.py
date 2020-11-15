from dcodex_variants.models import *

def run(*args):       
    classes_to_delete = [WitnessBase, Collection, Reading, Attestation,  LocationBase]

    for my_class in classes_to_delete:
        my_class.objects.all().delete()
