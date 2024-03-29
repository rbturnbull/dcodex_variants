from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.contrib.auth.mixins import PermissionRequiredMixin

from dcodex.util import get_request_dict

from dcodex.models import VerseTranscription

from . import models

from django.http import HttpResponse


#################################################
###    Index View 
#################################################

class IndexView(PermissionRequiredMixin, generic.TemplateView):
    template_name = "dcodex_variants/index.html"
    extra_context = dict(title="dcodex variants")
    permission_required = "dcodex_variants.view_collection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['collections'] = models.Collection.objects.all()
        context['witnesses'] = models.WitnessBase.objects.all()
        return context


#################################################
###    Collection Views 
#################################################

class CollectionListView(PermissionRequiredMixin, generic.ListView):
    model = models.Collection
    extra_context = dict(title="Collections")
    permission_required = "dcodex_variants.view_collection"
    # pagination = 50


class CollectionDetailView(PermissionRequiredMixin, generic.DetailView):
    model = models.Collection
    permission_required = "dcodex_variants.view_collection"
    slug_field = 'pk' # change to slug


#################################################
###    Location Views 
#################################################

class LocationDetailView(PermissionRequiredMixin, generic.DetailView):
    model = models.Location
    permission_required = "dcodex_variants.view_collection"
    template_name = "dcodex_variants/location_detail.html"
    context_object_name = "location"

    def get_object(self, queryset=None):
        collection = models.Collection.objects.get(pk=self.kwargs['collection_pk'])
        return collection.locations().filter(pk=self.kwargs['pk']).first()



#################################################
###    Witness Views 
#################################################

class WitnessDetailView(PermissionRequiredMixin, generic.DetailView):
    model = models.WitnessBase
    permission_required = "dcodex_variants.view_collection"
    template_name = "dcodex_variants/witness_detail.html"
    context_object_name = "witness"

    def get_object(self, queryset=None):
        return models.WitnessBase.objects.get(pk=self.kwargs['pk'])


class WitnessListView(PermissionRequiredMixin, generic.ListView):
    model = models.WitnessBase
    extra_context = dict(title="Witnesses")
    permission_required = "dcodex_variants.view_collection"
    template_name = "dcodex_variants/witness_list.html"




#################################################
###    Other Views 
#################################################

@login_required
def index(request):
    return HttpResponse("Hello, world. You're at the DCodex Variants index.")


@login_required
def location_for_witness(request, witness_slug, location_id):
    location = get_object_or_404(models.LocationUBS, id=location_id)

    manuscripts = []
    transcriptions = []
    witness = models.FamilyWitness.objects.filter(family__name=witness_slug).first()

    if witness:
        manuscripts = witness.family.manuscripts_at(location.start_verse)
        transcriptions = witness.family.transcriptions_at(location.start_verse)

    if not witness:
        manuscript = models.Manuscript.find(witness_slug)
        if manuscript:
            witness = models.ManuscriptWitness.objects.filter(manuscript=manuscript).first()
            manuscripts = models.Manuscript.objects.filter(id=manuscript.id)
            transcriptions = [manuscript.transcription(location.start_verse)]

    if not witness:
        witness = models.SiglumWitness.objects.filter(siglum=witness_slug).first()

    if witness:
        attestation = witness.attestations_at(location).first()
        text = attestation.text if attestation else ""
        info = attestation.info if attestation else ""

        return render(
            request,
            "dcodex_variants/location_for_familywitness.html",
            {
                "location": location,
                "witness": witness,
                "manuscripts": manuscripts,
                "text": text,
                "info": info,
                "transcriptions": transcriptions,
            },
        )

    return HttpResponse(f"Cannot find witness: {witness_slug}")


@login_required
def next_location_for_witness(request, witness_slug):
    witness = models.FamilyWitness.objects.filter(family__name=witness_slug).first()
    if not witness:
        manuscript = models.Manuscript.find(witness_slug)
        if manuscript:
            witness = models.ManuscriptWitness.objects.filter(manuscript=manuscript).first()

    if not witness:
        raise Exception(f"Cannot find witness {witness}")

    attested_location_ids = models.Attestation.objects.filter(witness=witness).values_list(
        "reading__location__id", flat=True
    )

    location = models.LocationBase.objects.exclude(id__in=attested_location_ids).first()

    if location:
        return location_for_witness(request, witness_slug, location.id)

    raise Exception(f"Cannot find locations for witness {witness}")


@login_required
def attestations(request):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get("reading_id")
    location_id = request_dict.get("location_id")
    location = get_object_or_404(models.Location, id=location_id)

    return HttpResponse(html)


@login_required
def remove_attestation(request):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get("reading_id")
    reading = get_object_or_404(models.Reading, id=reading_id)

    witness_id = request_dict.get("witness_id")
    witness = get_object_or_404(models.WitnessBase, id=witness_id)

    witness.remove_attestation(reading=reading)
    return HttpResponse("OK")


@login_required
def set_attestation(request):
    request_dict = get_request_dict(request)

    reading_id = request_dict.get("reading_id")
    reading = get_object_or_404(models.Reading, id=reading_id)

    witness_id = request_dict.get("witness_id")
    witness = get_object_or_404(models.WitnessBase, id=witness_id)

    response = witness.set_attestation(
        reading=reading, text=request_dict.get("text"), info=request_dict.get("info")
    )
    # response = 1
    return HttpResponse("OK" if response else "FAIL")


@login_required
def set_contra(request):
    request_dict = get_request_dict(request)

    transcription = get_object_or_404(
        VerseTranscription, id=request_dict.get("transcription_id")
    )
    witness = get_object_or_404(models.FamilyWitness, id=request_dict.get("witness_id"))

    attestations = models.Attestation.objects.filter(
        witness=witness, reading__location__id=request_dict.get("location_id")
    )
    for attestation in attestations:
        models.Contra.objects.get_or_create(
            attestation=attestation,
            manuscript=transcription.manuscript,
            verse=transcription.verse,
        )

    return HttpResponse("OK")


@login_required
def remove_contra(request):
    request_dict = get_request_dict(request)

    transcription = get_object_or_404(
        VerseTranscription, id=request_dict.get("transcription_id")
    )
    witness = get_object_or_404(models.FamilyWitness, id=request_dict.get("witness_id"))

    attestations = models.Attestation.objects.filter(
        witness=witness, reading__location__id=request_dict.get("location_id")
    )
    for attestation in attestations:
        models.Contra.objects.filter(
            attestation=attestation,
            manuscript=transcription.manuscript,
            verse=transcription.verse,
        ).delete()

    return HttpResponse("OK")
