import re
from pathlib import Path
from dcodex_bible.models import BibleVerse
from dcodex_variants.models import Collection, Location, Attestation, Reading
from lxml import etree as ET
from lxml.etree import _ElementTree as ElementTree
from lxml.etree import _Element as Element

from django.core.management.base import BaseCommand, CommandError

def read_tei(path:Path) -> ElementTree:
    parser = ET.XMLParser(remove_blank_text=True)
    with open(path, 'r') as f:
        return ET.parse(f, parser)


def extract_text(node:Element, include_tail:bool=True) -> str:
    if node is None:
        return ""
    
    tag = re.sub(r"{.*}", "", node.tag)

    if tag in ["pc", "witDetail", "note"]:
        return ""
    if tag == "app":            
        lemma = find_element(node, ".//lem")
        if lemma is None:
            lemma = find_element(node, ".//rdg")
        return extract_text(lemma) or ""


    text = node.text or ""
    for child in node:
        text += " " + extract_text(child)

    if include_tail and node.tail:
        text += " " + node.tail

    return text.strip()


def find_element(doc:ElementTree|Element, xpath:str) -> Element|None:
    assert doc is not None, f"Document is None in find_element({doc}, {xpath})"
    if isinstance(doc, ElementTree):
        doc = doc.getroot()
    namespaces = doc.nsmap | {"xml": "http://www.w3.org/XML/1998/namespace"}
    element = doc.find(xpath, namespaces=namespaces)
    if element is None:
        try:
            element = doc.find(xpath)
        except SyntaxError:
            return None
    return element


def find_elements(doc:ElementTree|Element, xpath:str) -> Element|None:
    if isinstance(doc, ElementTree):
        doc = doc.getroot()
    namespaces = doc.nsmap | {"xml": "http://www.w3.org/XML/1998/namespace"}
    results = doc.findall(xpath, namespaces=namespaces)
    results += doc.findall(xpath)
    return results


class Command(BaseCommand):
    help = "Imports variants from a TEI XML apparatus."

    def add_arguments(self, parser):
        parser.add_argument(
            "TEI",
            type=str,
            help="A TEI XML file.",
        )

    def handle(self, *args, **options):
        tei_path = Path(options["TEI"])

        collection, _ = Collection.objects.update_or_create(
            name=tei_path.name,
        )
        tei_tree = read_tei(tei_path)
        for rank, app in enumerate(find_elements(tei_tree, "app")):
            identifier = app.attrib.get("n", "")
            # B10K1V6U20-24
            if match := re.match(r"B(\d+)K(\d+)V(\d+)"):
                book = int(match.group(1)) + 39  # number of books in OT
                chapter = int(match.group(2))
                verse_num = int(match.group(3))
                start_verse = BibleVerse.get_from_values(book, chapter, verse_num)
                end_verse = start_verse
            else:
                breakpoint()
                # start_verse = 
                # end_verse = 

            location, _ = Location.objects.update_or_create(
                collection=collection,
                identifier=identifier,
                defaults=dict(
                    start_verse=start_verse,
                    end_verse=end_verse,
                    rank=rank,
                ),
            )
            for rdg in find_elements(app, "rdg"):
                reading_text = extract_text(rdg)
                reading, _ = Reading.objects.update_or_create(
                    identifier=rdg.attrib.get("n", ""),
                    location=location,
                    defaults=dict(
                        text=reading_text,
                    ),
                )

                for witness_name in reading.attrib["wit"].split():
                    # check if there is a corrector
                    if witness_name.endswith("C"):
                        siglum = witness_name[:-1]
                        corrector = 1
                    elif match := re.match(r"(.*)C(\d+)$", witness_name):
                        siglum = match.group(1)
                        corrector = int(match.group(2))
                    elif witness_name.endswith("*"):
                        siglum = witness_name[:-1]
                        corrector = 0
                    else:
                        siglum = witness_name
                        corrector =  0

                    attestation, _ = Attestation.objects.update_or_create(
                        witness=siglum,
                        reading=reading,
                        corrector=corrector,
                    )

        print("Success!")

            # <app xml:id="B10K4V922-V10U22">

            # <app xml:id="B10K1V6U20-24">
            #     <lem><w>εν</w><w>τω</w><w>ηγαπημενω</w></lem>
            #     <rdg n="1" wit="2085 223 1863 42 1896 912 390 234 1834 Lach NA28 1913 BasilOfCaesarea Origen Theodoret P46 01 02 03 06C2 018 020 025 044 056 075S 0142 0150 0151 0319C0 1 6 18 33 35 38 61 69 81 93 94 102 104 177 181 203 218 263 296 322 326 337 363 365 383 398 424 436 442 462 467 506 606 636 664 665 915 1069 1108 1115 1127 1175 1240 1241 1245 1311 1319 1490 1505 1509 1573 1611 1617 1678 1718 1721 1729 1739 1751 1831 1836 1837 1838 1840 1851 1860 1877 1881 1886 1893 1908 1910/1 1910/3 1912 1939 1959 1962 1963 1985 1987 1991 1996 1999 2005 2008 2011 2012 2127 2138 2180 2243 2344 2352 2464 2492 2523 2544 2805 2865S L156 L169/2 L587 L809 L1159 L1188 L1440 L2010 L2058 syrhmg RP SBL TH TR Tisch Treg WH"><w>εν</w><w>τω</w><w>ηγαπημενω</w></rdg>
            #     <rdg n="1-v1" type="reconstructed" wit="459"><w>εν</w><w>τω</w><w>ηγαπ<unclear>η</unclear>μενω</w></rdg>
            #     <rdg n="1-v2" type="reconstructed" wit="256"><w>εν</w><w>τω</w><w>ηγαπη<supplied reason="lacuna">μενω</supplied></w></rdg>
            #     <rdg n="1-v3" type="reconstructed" wit="L169/1"><w>εν</w><w>τω</w><w>ηγ<unclear>α</unclear>πημενω</w></rdg>
            #     <rdg n="1-f1" type="defective" cause="linguistic-confusion" ana="#LingConf" wit="2495"><w>εν</w><w>τω</w><w>αγαπημενω</w></rdg>
