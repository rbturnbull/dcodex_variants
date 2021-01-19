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
    help = 'Imports variants from the UBS5 apparatus.'

    def add_arguments(self, parser):
        parser.add_argument('UBS_HTML_FILE', type=str, help="An HTML file taken from the UBS5 apparatus in Logos.")

    def handle(self, *args, **options):
        ubs_html_file = options["UBS_HTML_FILE"]

        collection, _ = Collection.objects.update_or_create( name=os.path.basename(ubs_html_file) )
        rank = 0

        count = 0
        witnesses_counter = Counter()

        
        with open(ubs_html_file, 'r') as f:
            soup = BeautifulSoup(f, features="html.parser")
            #print(soup.prettify())
            paragraphs = soup.find_all('p')

            
            current_verse = None
            
            for paragraph in paragraphs:
                bold = paragraph.find('b')
                if bold:
        #            print(bold.string)
                    current_verse_string = bold.string
                    current_verse = BibleVerse.get_from_string( current_verse_string )
                    if not current_verse:
                        print("Cannot find verse:", current_verse_string)
                        sys.exit()
                    continue
                
                if "{" in paragraph.text:
                    print()
                    print('--------')
                    print()
                    print( current_verse )


                    
                    current_location, _ = LocationUBS.objects.get_or_create( start_verse=current_verse, rank=rank, collection=collection, defaults={
                        'apparatus_html' : str(paragraph)
                    } )

                    count += 1
                    rank += 1
                    
                    paragraph_text = str(paragraph)
                    
                    m = re.match( "\{(.)\}", paragraph.text )
                    certainty = m.group(1) if m else None
                    print('certainty', certainty)
                    
                    print(":")

                    
                    current_location.set_category_from_label( certainty )
                    current_location.save()

                    paragraph_text = paragraph_text.replace( " Γ ", " 036 " )
                    paragraph_text = paragraph_text.replace( " Δ ", " 037 " )
                    paragraph_text = paragraph_text.replace( " Θ ", " 038 " )
                    paragraph_text = paragraph_text.replace( " Λ ", " 039 " )                
                    paragraph_text = paragraph_text.replace( " Ξ ", " 040 " )
                    paragraph_text = paragraph_text.replace( " Π ", " 041 " )
                    paragraph_text = paragraph_text.replace( " Σ ", " 042 " )
                    paragraph_text = paragraph_text.replace( " Φ ", " 043 " )
                    paragraph_text = paragraph_text.replace( " Ψ ", " 044 " )
                    paragraph_text = paragraph_text.replace( "<i>f</i><sup>1</sup>", "ƒ1" )                    
                    paragraph_text = paragraph_text.replace( "<i>f</i><sup>13</sup>", "ƒ13" )                    



                    
                    readings = paragraph_text.split("//")
                    for reading in readings:
                        import_reading_from_html(current_location, reading)


        print("Success!")