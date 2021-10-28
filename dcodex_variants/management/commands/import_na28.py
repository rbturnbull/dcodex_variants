import sys
import re
import regex
from collections import Counter
from dcodex_bible.models import BibleVerse
from dcodex_variants.models import *
import os

from django.core.management.base import BaseCommand, CommandError


def import_na28(collection, book_name, na28_html_file):
    witness_count = Counter()

    rearrangement = '<p class="p3"><span class="s2">⸉</span>'

    known_readings = {
        "</span> <i>txt</i>": "txt",
        "</span> corrumpit": "corrumpit",
        '<span class="s2">⸆</span> <i>hic</i> <i>vss</i> 34/35 <i>add.</i>': "⸆ hic vss. 34/35 add.",
        '<span class="s2">⸀</span> φορεσωμεν (+ δη <span class="s1">𝔓</span><sup>46</sup>)': "φορεσωμεν (+ δη)",
        "</span> ουτε γαρ <i>7–9 1–5</i>": "ουτε γαρ <i>7–9 1–5</i>",
        "</span> <i>7–11 6 1–5</i>": "<i>7–11 6 1–5</i>",
        "</span> ουτε γαρ <i>2–8</i> περισσευομεν": "ουτε γαρ <i>2–8</i> περισσευομεν",
        '<span class="s2">⸆</span> <i>bis</i> μοι': "⸆ <i>bis</i> μοι",
        '<p class="p3">°<sup>1</sup>': "°1",
        '<p class="p3">°<sup>2</sup>': "°2",
        '<p class="p3"><span class="s2">⸁</span> (<i>ex itac.</i>?) οφειλετε': "⸁ (<i>ex itac.</i>?) οφειλετε",
        "⸀ θεω et ⸁ Χριστω": "⸀ θεω et ⸁ Χριστω",
        '<p class="p3"><span class="s2">⸉</span> <sup>1</sup>': "⸉1",
        '<p class="p3"><span class="s2">⸉</span> <sup>2</sup>': "⸉2",
        '<p class="p3"><span class="s2">⸀</span> (<i>ex itac.</i>?) ιδωμεν': "⸀ (<i>ex itac.</i>?) ιδωμεν",
        "</span> Παυλος τις δε (+ ο 1505. 2495) Απολλως (Απολλω 1241)": "Παυλος τις δε (+ ο 1505. 2495) Απολλως (Απολλω 1241)",
        "</span> <i>1–4 9 6–8 5</i>": "</span> <i>1–4 9 6–8 5</i>",
        "</span> ινα τις κενωσει (<i>vel</i> κενωση)": "</span> ινα τις κενωσει (<i>vel</i> κενωση)",
        '<span class="s2">⸀</span> κρειττονα (<i>vel</i> κρεισσονα)': '<span class="s2">⸀</span> κρειττονα (<i>vel</i> κρεισσονα)',
        '<span class="s2">⸆</span> και του (− 629) ενος (− D) ποτηριου': '<span class="s2">⸆</span> και του (− 629) ενος (− D) ποτηριου',
    }

    disallowed_reading_context = [
        "1881. 2464 𝔪 (sine acc.",
        "326. 614. 945. 2464 pm",
        "B D1 6. 629. 945 pm;",
        "1505 𝔪 syh (p. vs",
        "614. 629. 1241. 1505 pm",
        "365. 1175. 1505. 1881. 2464 pm",
        "1175. 1241. 1739c. 2495 pm",
        "1175. 1241. 1505. 1881. 2464 (sine acc.",
        "629. 1241. 2464 d (sine acc.",
        "104. 365. 614. 1881 f g (sine acc.",
        "D F G L Ψ 81. 1241. 1505. 1506. 1881. 2464. l",
        "1175. 1241. 1505. 1506. 1739. 1881*vid. l",
        "0289. 6. 33. 81. 614. 1175. 1241. 2464. l",
        "365. 630. 1175. 1241. 1506. 1739. 2464. l",
        "D F G L P 0289. 1241. 1506. 1881. 2464 pm",
    ]

    disallowed_witnesses = [
        "<i>pm</i>",
        "<i>l</i>",
        "D<sup>s</sup>",
        "pt</sup>",
        "<span",
        'class="s2">⸂</span>)',
        "<i>pm;</i>",
        "1–5</i>",
        "<i>sine",
        "vid</sup>",
        "ℵC",
        "",
        "<i>7–9",
        "v.l.</sup>",
        "sy<sup>p.h**</sup>",
        "D*<sup>.c</sup>",
        "D*<sup>.2</sup>",
        "Ir<sup>lat</sup>",
        "<sup>p</sup>",
        "lat</sup>",
        "ℵ<sup></sup>*<sup>.1</sup>",
        "bo?",
        "ℵ<sup>2a</sup>",
        "D<sup>1vid</sup>",
        "sy<sup>p.hmg</sup>",
        "A<sup></sup>*<sup>.c</sup>",
        "B<sup></sup>*<sup>.2</sup>",
        "D<sup></sup>*<sup>.1</sup>",
        "P46c2",
        "Ir<sup>lat</sup><sup>v.l.</sup>",
        "P46c1",
        "sy<sup>p.h</sup>",
        "<i>ex",
        "lat.</i>?",
        "D*<sup>.1</sup>",
        "D<sup>2vid</sup>",
        "Ir<sup>arm",
        "<i>txt</i>",
        "945<sup>v.l.</sup>",
        "Ir<sup>gr",
        "Ophites<sup>Ir",
        "BC<sup>2vid</sup>",
        "D<sup></sup>*<sup>.2</sup>",
        "sy<sup>h**</sup>",
        "P61vid",
        "sy__p sy__h*",
        "D<sup>2<\\/sup>",
        "D<sup>c<\\/sup>",
        "D<sup>1<\\/sup>",
        "ℵ<sup>1<\\/sup>",
        "sy__p sy__hmg",
        "A<sup>c<\\/sup>",
        "B<sup>2<\\/sup>",
        "sy__p sy__h",
        "Ophites<sup>Ir_lat</sup>",
        "sy__h*",
    ]

    rank = 0

    with open(na28_html_file, "r") as f:
        text = f.read()

        text = text.replace(
            '</p>\n<p class="p4"><span class="s4">¦</span>',
            '</p><p class="p4"><span class="s4">¦</span>',
        )
        text = text.replace(
            '<span class="s2">⸀</span> θεω <i>et</i></p>\n<p class="p3"><span class="s2">⸁</span> Χριστω',
            "⸀ θεω et ⸁ Χριστω",
        )

        text = text.replace('<span class="s3">א</span>C', "ℵ C")
        text = text.replace('<span class="s3">א</span>', "ℵ")
        text = text.replace('<span class="s1">𝔪</span>', "𝔪")
        # text = text.replace('<span class="s1">𝔓</span><sup>', "P")
        text = text.replace('</p><p class="p4"><span class="s4">', "")

        # Hack for 1 Cor 7:28
        text = text.replace("(<i>ex lat.</i>?)", "")

        # There is something funny in 1 Cor 13:4
        text = text.replace(
            '[<span class="s4">:</span> , <i>et</i> <span class="s4"><sup>:</sup></span><sup>1</sup> −]</p>\n<p class="p3">',
            "",
        )

        text = re.sub(r"\(<i>cf</i>.*?\)", "", text)

        text = re.sub(
            r"(.)<sup>\(</sup>\*<sup>\).([c\d])</sup>", r"\1* \1<sup>\2</sup>", text
        )
        text = re.sub(r"(.)<sup></sup>\*<sup>.c</sup>", r"\1* \1<sup>c</sup>", text)
        text = re.sub(r"(.)\*<sup>.([c\d])</sup>", r"\1* \1<sup>\2</sup>", text)

        verses = text.split('<p class="p2"><b>')

        verses = verses[1:]
        print(verses)
        verse_ref = ""
        current_chapter = None
        current_verse = None
        for verse in verses:
            print("------------")

            if m := re.match(r"([\d\,\/]*)<\/b>(.*)", verse, re.DOTALL):
                verse = m.group(2)
                verse_ref = m.group(1)

                if "," in verse_ref:
                    current_chapter = int(verse_ref.split(",")[0])
                    current_verse = int(verse_ref.split(",")[1])
                    current_verse_end = current_verse
                else:
                    if m := re.match("(\d+)/(\d+)", verse_ref):
                        current_verse = int(m.group(1))
                        current_verse_end = int(m.group(2))
                    else:
                        current_verse_end = current_verse = int(verse_ref)

            current_verse_start_obj = BibleVerse.get_from_string(
                f"{book_name} {current_chapter}:{current_verse}"
            )
            if current_verse_end and current_verse_end != current_verse:
                current_verse_end_obj = BibleVerse.get_from_string(
                    f"{book_name} {current_chapter}:{current_verse_end}"
                )
            else:
                current_verse_end_obj = None

            print(current_verse_start_obj)

            variation_units = verse.strip().split("\n")
            for variation_unit_index, variation_unit in enumerate(variation_units):
                # print("\t",variation_unit_index, variation_unit[:40])
                print(
                    f"\t--variation unit {current_chapter}:{current_verse}. {variation_unit_index}"
                )

                current_location, _ = LocationUBS.objects.get_or_create(
                    start_verse=current_verse_start_obj,
                    rank=rank,
                    collection=collection,
                    defaults={
                        "apparatus_html": str(variation_unit),
                        "end_verse": current_verse_end_obj,
                    },
                )

                rank += 1

                # Hack for 1 Corinthians 12:26
                if "A B 1739 <i>txt</i>" in variation_unit:
                    variation_unit = variation_unit.replace(
                        "A B 1739 <i>txt</i>", "A B 1739 ¦</span> <i>txt</i>"
                    )

                if "A B 1739 <i>txt</i>" in variation_unit:
                    raise Exception("in")

                readings = variation_unit.split("¦")
                for reading_app in readings:
                    reading = None
                    reading_found = ""

                    if "</body>" in reading_app or "</html>" in reading_app:
                        break

                    if "<i>sine test." in reading_app:
                        continue

                    print("reading_app raw:", reading_app)

                    for r in known_readings:
                        if reading_app.startswith(r):
                            reading = known_readings[r]
                            reading_app = reading_app[len(r) :]
                            reading_found = "known"

                    if reading == None:
                        if reading_app[0] == "°":
                            reading = "°"
                            reading_app = reading_app[1:]
                        elif m := re.match(
                            r"(.*?[[α-ωἤῶ][α-ωἤῶ ]*<i>.+?<\/i>)(.*)", reading_app
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                            reading_found = "Greek with italics"
                        elif m := re.match(
                            r"(.*?[[α-ωἤῶΧ][α-ωἤῶΧ ]*\([α-ωἤΧῶ\+\−].+?\)[α-ωἤΧῶ ]*)(.*)",
                            reading_app,
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                            reading_found = "Greek with brackets"
                        elif m := regex.match(
                            r"(.*[α-ωἤῶ])(.*)", reading_app, re.DOTALL
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                            reading_found = "Greek"
                        elif m := re.match(
                            r"(<span class=\"s2\">[⸉⸂⸄].*?<\/i>)(.*)", reading_app
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                            reading_found = "siglum with italics"
                        elif m := re.match(
                            r"(<p class=\"p3\"><span class=\"s2\">⸄<\/span> .*</i>)(.*)",
                            reading_app,
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                        elif m := re.match(r".*°(.*)", reading_app):
                            reading = "°"
                            reading_app = m.group(1)
                        elif m := re.match(r".*⸋(.*)", reading_app):
                            reading = "⸋"
                            reading_app = m.group(1)
                            reading_found = "square"
                        elif m := re.match(r"(.*?\−)(.*)", reading_app):
                            reading = m.group(1)
                            reading_app = m.group(2)
                            reading_found = "dash"
                        elif reading_app.startswith(rearrangement):
                            reading = "⸉"
                            reading_app = reading_app[len(rearrangement) :]
                            reading_found = "rearrangement"
                        elif m := re.match(r".*⸉(.*)", reading_app):
                            reading = "⸉"
                            reading_app = m.group(1)
                            reading_found = "sigla"
                        elif m := re.match(
                            r'<span class="s2">⸂<\/span> (<i>.*<\/i>)(.*)', reading_app
                        ):
                            reading = m.group(1)
                            reading_app = m.group(2)
                        elif m := re.match(r"<\/span> (<i>.*<\/i>)(.*)", reading_app):
                            reading = m.group(1)
                            reading_app = m.group(2)

                        if m := re.match(r"(.*)(ℵ.*)", reading):
                            reading = m.group(1)
                            reading_app = m.group(2) + reading_app

                        if m := re.match(r"(.*)(P\d.*)", reading):
                            reading = m.group(1)
                            reading_app = m.group(2) + reading_app

                    if reading == None:
                        raise Exception(f"Cannot parse reading: {reading_app}")

                    print("READING:", reading)
                    print("reading_app after reading:", reading_app)

                    witness_substitutions = {
                        r"sy<sup>(h|p|ph|hmg|h\*\*)<\/sup>": r"sy__\1",
                    }

                    reading = re.sub(r"<.*?>", "", reading)
                    print(f"\t\t{reading}")

                    for disallowed_reading in disallowed_reading_context:
                        if disallowed_reading in reading:
                            raise Exception(
                                f"Disallowed reading: {reading}. reading found {reading_found}"
                            )

                    if "(" in reading and ")" not in reading:
                        raise Exception(
                            f"Disallowed reading: {reading}. Brackets uneven. reading found {reading_found}"
                        )

                    current_reading_obj, _ = Reading.objects.update_or_create(
                        text=reading, location=current_location
                    )

                    if reading == "txt":
                        current_location.ausgangstext = current_reading_obj
                        current_location.save()

                    # Sometimes the superscript values are delimited with
                    if m := re.match(r".*?𝔓</span><sup>(.*?)<\/sup>(.*)", reading_app):
                        papyri = m.group(1).split(".")
                        reading_app = ""
                        for papyrus in papyri:
                            reading_app += f" P{papyrus}"
                        reading_app += m.group(2)
                        reading_app = reading_app.strip()
                        # reading_app = m.group(1) + m.group(2).replace(".", " ") + m.group(2)

                    # Lectionaries
                    reading_app = re.sub(r"<i>l<\/i> (\d)", r"l\1", reading_app)

                    # permulti
                    # cf. p60*
                    reading_app = reading_app.replace(" <i>pm</i>", "")
                    reading_app = reading_app.replace(" <i>pm;</i>", "")
                    reading_app = reading_app.replace(
                        " vid</sup>", "</sup><sup>vid</sup>"
                    )
                    reading_app = reading_app.replace(
                        " pt</sup>", "</sup><sup>pt</sup>"
                    )
                    reading_app = reading_app.replace(
                        " v.l.</sup>", "</sup><sup>v.l.</sup>"
                    )

                    # Hack for 1 Cor 15:54
                    reading_app = reading_app.replace(
                        "(την <i>a.</i> αθανασιαν ℵ A 088. 33 <i>et</i> <i>a.</i> αφθαρσιαν 33)",
                        "ℵ A 088. 33",
                    )

                    # Get rid of alt greek
                    reading_app = re.sub(r"\([\+\−α-ωἤῶ ]+(.*?)\)", r"\1", reading_app)
                    reading_app = re.sub(
                        r'\(<span class="s2">⸉<\/span>(.*?)\)', r"\1", reading_app
                    )

                    reading_app = reading_app.replace(
                        "Ir<sup>arm, lat pt</sup>", "Ir__arm_lat_pt"
                    )
                    reading_app = reading_app.replace(
                        "Ir<sup>arm, lat</sup><sup>pt</sup>", "Ir__arm_lat_pt"
                    )
                    reading_app = reading_app.replace(
                        "Ir<sup>gr, lat</sup><sup>pt</sup>", "Ir__gr_lat_pt"
                    )

                    reading_app = reading_app.replace(
                        "Ophites<sup>Ir lat</sup>", "Ophites<sup>Ir_lat</sup>"
                    )

                    reading_app = re.sub(
                        r"sy<sup>(h|p|ph|hmg|h\*\*)\.(h|p|ph|hmg|h\*\*)<\/sup>",
                        r"sy__\1 sy__\2",
                        reading_app,
                    )

                    reading_app = reading_app.replace("sy <sup>", "sy<sup>")

                    witnesses = reading_app.strip().split()
                    witnesses_clean = []
                    suffixes = [".", "</p>", ";"]
                    for witness in witnesses:
                        corrector = None
                        notes = ""
                        if witness == "</span>" or witness == "</p>":
                            continue

                        # Get rid of brackets
                        witness = witness.replace("(", "").replace(")", "")
                        if witness.strip() == "":
                            continue

                        for subs, replace in witness_substitutions.items():
                            witness = re.sub(subs, replace, witness)

                        for suffix in suffixes:
                            if witness.endswith(suffix):
                                witness = witness[: -len(suffix)]

                        if witness in witness_substitutions:
                            witness = witness_substitutions[witness]

                        if m := re.match(r"vg<sup>(mss?)<\/sup>", witness):
                            witness = f"vg"
                            notes = m.group(1)

                        if m := re.match(r"vg<sup>(.*)<\/sup>", witness):
                            witness = f"vg__{m.group(1)}"

                        if m := re.match(r"^(P\d+)<\/sup>$", witness):
                            witness = m.group(1)

                        if m := re.match(r"^(P\d+)vid(<\/sup>)?$", witness):
                            witness = m.group(1)
                            notes = "vid"

                        if m := re.match(r"(.*)<sup>c</sup>$", witness):
                            witness = m.group(1)
                            corrector = 1

                        if m := re.match(r"(.*\d)c$", witness):
                            witness = m.group(1)
                            corrector = 1

                        if m := re.match(r"(.*)<sup>mg</sup>$", witness):
                            witness = m.group(1)
                            corrector = "1"  # CORRECTOR HACK
                            notes = "mg"

                        if m := re.match(r"(.*)<sup>2a</sup>$", witness):
                            witness = m.group(1)
                            corrector = "2a"
                            corrector = 2  # CORRECTOR HACK

                        if m := re.match(r"(.*)<sup>1vid</sup>$", witness):
                            witness = m.group(1)
                            corrector = "1"
                            notes = "vid"

                        if witness == "D<sup>s</sup>":
                            witness = "D__s"
                            notes = "supplement"

                        if m := re.match(r"(.*)<sup>txt</sup>$", witness):
                            witness = m.group(1)
                            notes = "txt"

                        if m := re.match(r"(.*)<sup>vid<\/sup>", witness):
                            witness = m.group(1)
                            notes = "vid"

                        if witness == "Ir<sup>lat</sup>" or witness == "Ir<sup>lat":
                            witness = "Ir"
                            notes = "lat"

                        if witness == "Ir<sup>arm</sup>":
                            witness = "Ir"
                            notes = "arm"

                        if witness == "Or<sup>1739mg</sup>":
                            witness = "Or"
                            notes = "1739mg"

                        if witness == "Ir__arm_lat_pt":
                            witness = "Ir"
                            notes = "arm, lat pt"

                        if witness == "Ir__gr_lat_pt":
                            witness = "Ir"
                            notes = "gr, lat pt"

                        if witness == "Ir<sup>lat</sup><sup>pt</sup>":
                            witness = "Ir"
                            notes = "lat pt"

                        if m := re.match(r"(.*)<sup>(\d+)<\/sup>", witness):
                            witness = m.group(1)
                            corrector = int(m.group(2))

                        if m := re.match(r"(.*)<sup>pt<\/sup>", witness):
                            witness = m.group(1)
                            motes = "in part"

                        if m := re.match(r"(.*)<sup>ms<\/sup>", witness):
                            witness = m.group(1)
                            notes = "Manuscript"

                        if m := re.match(r"(.*)<sup>mss<\/sup>", witness):
                            witness = m.group(1)
                            notes = "Manuscripts"

                        if m := re.match(r"(.*)<sup>Ir<\/sup>", witness):
                            witness = m.group(1)
                            notes = "According to Irenaeus"

                        if witness.endswith("*") and not witness.endswith("**"):
                            witness = witness[:-1]
                            notes = "Original"

                        if witness.endswith("c2"):
                            witness = witness[:-2]
                            corrector = 2

                        if witness.endswith("c1"):
                            witness = witness[:-2]
                            corrector = 1

                        if m := re.match(r"Mcion<sup>([TEA])<\/sup>", witness):
                            witness = "Mcion"
                            marcion_authorities = {
                                "E": "Epiphanius",
                                "T": "Tertullian",
                                "A": "Adamantius",
                            }
                            authority = marcion_authorities[m.group(1)]
                            notes = f"According to {authority}."

                        if witness == "Ir<sup>lat</sup><sup>v.l.</sup>":
                            witness = "Ir"
                            notes = "lat v.l."

                        if m := re.match("^(.*)<sup>(\d)vid</sup>$", witness):
                            witness = m.group(1)
                            corrector = m.group(2)
                            notes = "vid"

                        if witness.endswith("?"):
                            witness = witness[:-1]
                            notes = "Uncertain"

                        if m := re.match("(.*)<sup>v.l.<\/sup>", witness):
                            witness = m.group(1)
                            notes = "v.l."

                        if witness == "Ophites<sup>Ir_lat</sup>":
                            witness = "Ophites"
                            notes = "Ir lat"

                        if witness in disallowed_witnesses:
                            raise Exception(
                                f"Witness '{witness}' not allowed: From {reading_app}. \nWitnesses {witnesses}. reading_found {reading_found}. {witnesses_clean =}"
                            )

                        if re.search(r"[α-ωἤῶ]", witness):
                            print(witnesses, "witnesses")
                            print("reading_found", reading_found)
                            raise Exception(
                                f"Greek found in witness {witness}\nWitnesses {witnesses}. reading_found {reading_found}"
                            )

                        witness_count.update([witness])
                        witnesses_clean.append(witness)

                        if witness.endswith("."):
                            witness = witness[:-1]

                        witness_obj, _ = SiglumWitness.objects.update_or_create(
                            siglum=witness
                        )

                        Attestation.objects.update_or_create(
                            reading=current_reading_obj,
                            witness=witness_obj,
                            corrector=corrector,
                            defaults={
                                "info": notes,
                            },
                        )

                        if witness == "𝔪":
                            current_location.byz = current_reading_obj
                            current_location.save()

                    # print(f"\t\t\t{witnesses_clean}")
                    # witnesses

    witness_count.most_common()


class Command(BaseCommand):
    help = "Imports variants from the NA28 apparatus."

    def add_arguments(self, parser):
        parser.add_argument(
            "BOOK_NAME", type=str, help="The name of the biblical book being imported."
        )
        parser.add_argument(
            "NA28_HTML_FILE",
            type=str,
            help="An HTML file taken from the NA28 apparatus in Logos.",
        )
        parser.add_argument(
            "--flush",
            type=str,
            help="If 'yes', then it removes old locations in the collection before importing.",
        )

    def handle(self, *args, **options):
        na28_html_file = options["NA28_HTML_FILE"]

        collection, _ = Collection.objects.update_or_create(
            name=os.path.basename(na28_html_file)
        )

        if options["flush"].lower() == "yes":
            collection.locations().delete()

        import_na28(collection, options["BOOK_NAME"], na28_html_file)
