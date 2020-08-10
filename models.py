from django.db import models
from polymorphic.models import PolymorphicModel
from dcodex.models import Verse, Manuscript, Family


class WitnessBase(PolymorphicModel):
    def attests_reading(self, reading, corrector=None):
        return Attestation.objects.filter( reading=reading, witness=self, corrector=corrector ).count() > 0

    def set_attestation(self, reading, corrector=None, info=None, text=None):
        attestation, _ = Attestation.objects.update_or_create( reading=reading, witness=self, corrector=corrector, defaults={
            'info':info, 
            'text':text,
        })
        return attestation

    def remove_attestation(self, reading, corrector=None):
        Attestation.objects.filter( reading=reading, witness=self, corrector=corrector ).all().delete()

    def attestations_at(self, location, corrector=None):
        return Attestation.objects.filter(witness=self, reading__location=location, corrector=corrector)


class SiglumWitness(WitnessBase):
    siglum = models.CharField(max_length=255)

    def __str__(self):
        return self.siglum


class ManuscriptWitness(WitnessBase):
    manuscript = models.ForeignKey( Manuscript, on_delete=models.CASCADE )

    def __str__(self):
        return str(self.manuscript)


class FamilyWitness(WitnessBase):
    family = models.ForeignKey( Family, on_delete=models.CASCADE )

    def __str__(self):
        return str(self.family)

class Collection(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def write_carlson( self, file, include_ubs=False ):
        # Write MSS in header
        witnesses = list(self.witnesses_set())
        if include_ubs:
            witnesses = ['UBS'] + witnesses
        file.write( "* %s ;\n" % " ".join( witnesses ) )
        file.write( "= $? $* ;\n" ) # Make all witnesses explicit
        
        for location in self.locations:
            file.write( "\n@ %s\n" % location.verse.replace(" ","") )
            file.write( "{{}\n" )
            file.write( "[ %s\n" % location.readings[0].text )  #UBS Reading
            file.write( "\t| %s \n" % " ".join([ format_reading(reading.text) for reading in location.readings[1:]]) ) 
            file.write( "]\n" )
            location_witnesses_counter = location.witnesses_counter()
            d = "<"
            for reading_index, reading in enumerate(location.readings):
                original_witnesses_names = [name for name in reading.original_witness_names() if location_witnesses_counter[name] == 1]
                if reading_index == 0 and include_ubs:
                    original_witnesses_names = ['UBS'] + original_witnesses_names
                file.write( "\t%s %d %s\n" % (d, reading_index, " ".join( original_witnesses_names )) )
                d = "|"
            file.write( "> }\n" )
    def witnesses_counter(self):
        counter = Counter()
        for location in self.locations:
            for reading in location.readings:
                for witness in reading.original_witnesses():
                    counter.update([witness.name])
        return counter
    def witnesses_set(self):
        s = set()
        for location in self.locations:
            for reading in location.readings:
                for witness in reading.original_witnesses():
                    s.add(witness.name)
        return s
            
            


class LocationBase(PolymorphicModel):
    start_verse = models.ForeignKey( Verse, on_delete=models.CASCADE, related_name="variant_start_verse" )
    end_verse = models.ForeignKey( Verse, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name="variant_end_verse" )
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField()

    def __str__(self):
        return str(self.start_verse)

    class Meta:
        ordering = ['collection', 'rank']

    def next(self):
        return type(self).objects.filter(collection=self.collection, rank__gt=self.rank).first()

    def prev(self):
        return type(self).objects.filter(collection=self.collection, rank__lt=self.rank).last()

class Location(LocationBase):
    pass


class LocationUBS(LocationBase):
    ausgangstext = models.ForeignKey('Reading', on_delete=models.SET_NULL, default=None, blank=True, null=True, related_name="ausgangstext_reading")
    byz = models.ForeignKey('Reading', on_delete=models.SET_NULL, default=None, blank=True, null=True, related_name="byz_reading")
    CategoryUBS = models.IntegerChoices('CategoryUBS', 'A B C D')
    category = models.IntegerField(choices=CategoryUBS.choices, default=None, blank=True, null=True)
    apparatus_html = models.TextField()

    def set_category_from_label(self, label):
        if label == None:
            self.category = None
        else:
            index = self.CategoryUBS.labels.index(label)
            value = self.CategoryUBS.values[index]
            self.category = value


class Reading(models.Model):
    text = models.TextField()
    location = models.ForeignKey(LocationBase, on_delete=models.CASCADE)

    def __str__(self):
        return self.text
    

class Attestation(models.Model):
    witness = models.ForeignKey( WitnessBase, on_delete=models.CASCADE )
    reading = models.ForeignKey( Reading, on_delete=models.CASCADE )
    text = models.TextField( default=None, null=True, blank=True )
    info = models.TextField( default=None, null=True, blank=True )
    corrector = models.PositiveIntegerField( default=None, null=True, blank=True )



