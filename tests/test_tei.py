from django.test import TestCase
from dcodex.models import Manuscript, Family, Verse
from dcodex_variants.models import SiglumWitness, Location, LocationUBS, Reading, Attestation, Collection
from dcodex_variants.tei import write_tei
from io import StringIO

class TEITest(TestCase):
    def test_tei(self):
        collection = Collection.objects.create(name="Test Collection")
        verses = [Verse.objects.create(rank=i) for i in range(10)]
        locations = [Location.objects.create(start_verse=verse, collection=collection, rank=0) for verse in verses]
        witnesses = [
            SiglumWitness.objects.create(siglum=str(i), origin_date_earliest=i, origin_date_latest=2 * i + 10) 
            for i in range(10)
        ]

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

        output = StringIO()
        write_tei(collection, output)
        output_str = output.getvalue()
        assert '<body>\n\t\t\t<app xml:id="L1__1" loc="1">\n\t\t\t\t<rdg wit="0 3 6 9" n="1-text_0_-_A">text 0 - A</rdg>' in output_str
        assert '<witness n="7">\n\t\t\t\t\t\t<origDate notBefore="7" notAfter="24" />' in output_str


