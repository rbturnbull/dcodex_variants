from django.test import TestCase
from dcodex.models import Manuscript, Family, Verse
from dcodex_variants.models import SiglumWitness, Location, LocationUBS, Reading, Attestation, Collection
from dcodex_variants.tei import write_tei

class TEITest(TestCase):
    def test_tei(self):
        collection = Collection.objects.create(name="Test Collection")
        verses = [Verse.objects.create(rank=i) for i in range(10)]
        locations = [Location.objects.create(start_verse=verse, collection=collection, rank=0) for verse in verses]
        witnesses = [SiglumWitness.objects.create(siglum=str(i)) for i in range(10)]

        reading_index = 0

        for location in locations:
            reading_a = Reading.objects.create(location=location, text=f"text {location.start_verse.rank} - A")
            reading_b = Reading.objects.create(location=location, text=f"text {location.start_verse.rank} - B")
            reading_c = Reading.objects.create(location=location, text=f"text {location.start_verse.rank} - c")
            readings = [reading_a, reading_b, reading_c]

            for witness in witnesses:
                reading = readings[reading_index % len(readings)]
                Attestation.objects.create(reading=reading, witness=witness)
                reading_index += 1

        write_tei(collection, "test_tei.xml")

        assert False