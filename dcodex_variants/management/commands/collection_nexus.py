from django.core.management.base import BaseCommand, CommandError
from dcodex_variants.models import *


class Command(BaseCommand):
    help = 'Imports variants from the UBS5 apparatus.'

    def add_arguments(self, parser):
        parser.add_argument('collection', type=str, help="The name of the collection to be exported.")
        parser.add_argument('outputfile', type=str, help="The path to the output file. Any existing file will be overwritten.")

    def handle(self, *args, **options):
        collection = Collection.objects.get( name=options["collection"] )
        collection.write_nexus( options["outputfile"] )
