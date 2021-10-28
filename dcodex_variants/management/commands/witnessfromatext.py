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
    help = "Creates a siglum."

    def add_arguments(self, parser):
        parser.add_argument(
            "collection", type=str, help="The collection of variation units to use."
        )
        parser.add_argument(
            "siglum", type=str, help="The siglum for the A-Text witness."
        )

    def handle(self, *args, **options):
        collection = Collection.objects.get(name=options["collection"])
        witness, _ = SiglumWitness.objects.update_or_create(siglum=options["siglum"])

        for location in collection.locations():
            if location.ausgangstext:
                Attestation.objects.filter(
                    reading__location=location, witness=witness
                ).delete()
                Attestation.objects.update_or_create(
                    witness=witness,
                    reading=location.ausgangstext,
                    info="Auto-generated from A-Text.",
                )
