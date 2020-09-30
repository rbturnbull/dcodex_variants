from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(Collection)    
class CollectionAdmin(admin.ModelAdmin):
    pass

@admin.register(LocationUBS)    
class LocationUBSAdmin(admin.ModelAdmin):
    raw_id_fields = ("start_verse","end_verse",)

@admin.register(Reading)    
class ReadingAdmin(admin.ModelAdmin):
    pass

@admin.register(SiglumWitness)    
class SiglumWitnessAdmin(admin.ModelAdmin):
    pass

@admin.register(FamilyWitness)    
class FamilyWitnessAdmin(admin.ModelAdmin):
    pass

@admin.register(ManuscriptWitness)    
class ManuscriptWitnessAdmin(admin.ModelAdmin):
    pass

@admin.register(Attestation)    
class AttestationAdmin(admin.ModelAdmin):
    pass

