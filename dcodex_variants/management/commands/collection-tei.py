from django.core.management.base import BaseCommand, CommandError
from dcodex_variants.models import *
from dcodex_variants.tei import write_tei


class Command(BaseCommand):
    help = "Exports a collection of variant readings as a NEXUS file for phylogenetic analysis."

    def add_arguments(self, parser):
        parser.add_argument(
            "collection", type=str, help="The name of the collection to be exported."
        )
        parser.add_argument(
            "outputfile",
            type=str,
            help="The path to the output file. Any existing file will be overwritten.",
        )
        parser.add_argument(
            "--min-locations",
            type=int,
            default=1,
            help="The minimum number of locations a witness has to attest for it to be included in the tei file.",
        )
        parser.add_argument(
            "--exclude-sigla",
            type=str,
            nargs='+',
            help="Sigla of witnesses to exclude from the tei file.",
        )

    def handle(self, *args, **options):
        collection = Collection.objects.get(name=options["collection"])
        write_tei(
            collection,
            options["outputfile"], 
            min_locations=options["min_locations"], 
            exclude_sigla=options["exclude_sigla"],
        )

    witnesses=None, 
    locations=None,
    subyz:bool=True,
    min_locations=1, 
    exclude_sigla=None,
    atext_witness:bool=False,
    atext_certainty_degree:int=5,
