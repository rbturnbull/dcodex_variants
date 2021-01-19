from django.core.management.base import BaseCommand, CommandError
from dcodex_variants.models import *

class Command(BaseCommand):
    help = 'Deletes all objects in the Witness, Collection, Reading, Attestation, and Location tables.'

    def handle(self, *args, **options):

        result = input("This will delete all objects in the Witness, Collection, Reading, Attestation, and Location tables. Are you sure you wish to continue? y/N: ")
        if not result.lower().startswith( "y" ):
            return 

        classes_to_delete = [WitnessBase, Collection, Reading, Attestation,  LocationBase]

        for my_class in classes_to_delete:
            my_class.objects.all().delete()



