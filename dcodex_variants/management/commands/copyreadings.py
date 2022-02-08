import sys
import re
from bs4 import BeautifulSoup
import regex
from collections import Counter
from dcodex_bible.models import BibleVerse
from dcodex_variants.models import *
import os

from dcodex_variants.import_ubs import *

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Copies readings from one witness from a list of others if the are not attested in those locations."

    def add_arguments(self, parser):
        parser.add_argument(
            "collection", type=str, help="The collection of locations to use. If not given then all locations are used.", default=None,
        )
        parser.add_argument(
            "siglum", type=str, help="The siglum witness to copy from."
        )
        parser.add_argument(
            "others", type=str, nargs='+', help="The sigla for other witnesses to copy to."
        )

    def handle(self, *args, **options):
        collection = Collection.objects.get(name=options["collection"])
        witness = SiglumWitness.objects.get(siglum=options["siglum"])
        others = [SiglumWitness.objects.get(siglum=siglum) for siglum in options["others"]]

        for location in witness.locations_attested(collection=collection):
            print(location)
            for attestation in witness.attestations_at(location):
                print('\t', attestation.reading)
                for other in others:
                    if not other.attestations_at(location):
                        print('\t\t', other)
                        Attestation(
                            witness=other,
                            reading=attestation.reading,
                            info=f"Copied from {witness}",
                        ).save()
