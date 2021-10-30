from django.core.management.base import BaseCommand, CommandError
from dcodex_variants.models import *


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
            help="The minimum number of locations a witness has to attest for it to be included in the nexus file.",
        )
        parser.add_argument(
            "--exclude-sigla",
            type=str,
            nargs='+',
            help="Sigla of witnesses to exclude from the nexus file.",
        )

    def handle(self, *args, **options):
        collection = Collection.objects.get(name=options["collection"])
        collection.write_nexus(options["outputfile"], min_locations=options["min_locations"], exclude_sigla=options["exclude_sigla"])
