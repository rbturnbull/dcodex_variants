from django.db import models
from polymorphic.models import PolymorphicModel
from dcodex.models import Verse, Manuscript, Family
import re
import numpy as np 

def category_from_siglum(siglum):
    if len(siglum) == 1 and siglum.isupper():
        return "Majuscule"
    if siglum.isdigit():
        if siglum[0] == "0":
            return "Majuscule"
        return "Minuscule"
    if siglum[0] == "P" and siglum[1:].isdigit():
        return "Papyrus"

    if siglum[0] == "𝑙":
        return "Lectionary"

    if siglum[0] == "ƒ":
        return "Minuscule"

    if "__" in siglum or siglum in ["vg", "arm", "eth", "geo", "slav"]:
        return "Version"

    if len(siglum) == 3 and siglum[:2] == "ar":
        return "Version"

    if "__" in siglum or siglum in ["NIV", "REB", "TOB", "BTI", "DHH", "EU", "LB", "BJ", "NBS", "GNB", "NRSV"]:
        return "Edition"

    if siglum in ["Byz", "mss", "Lect", "Latin-mss", "Greek-mss"]:
        return "Other"

    if siglum.title() == siglum:
        return "Father"

    return ""

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

    def reading_ids_at(self, location, corrector=None):
        return { attestation.reading.id for attestation in self.attestations_at(location, corrector) }

    def locations_attested( self, collection, corrector=None ):
       location_ids = Attestation.objects.filter(witness=self, reading__location__collection=collection, corrector=corrector).values_list('reading__location__id', flat=True).distinct()
       return LocationBase.objects.filter( id__in=location_ids)

    def agreement_array(self, other_witness, locations):
        results = np.zeros( (len(locations),), dtype=int )

        for index, location in enumerate( locations ):
            my_readings = self.reading_ids_at( location )
            other_readings = other_witness.reading_ids_at( location )
            if my_readings == other_readings:
                results[index] = 2
            elif len(my_readings.intersection(other_readings)) > 0 or len(my_readings) == 0 or len(other_readings) == 0:
                results[index] = 1
            else:
                print(location, location.id)
                results[index] = 0

        return results


class SiglumWitness(WitnessBase):
    siglum = models.CharField(max_length=255)

    def __str__(self):
        return self.siglum


class ManuscriptWitness(WitnessBase):
    manuscript = models.ForeignKey( Manuscript, on_delete=models.CASCADE )

    def __str__(self):
        return str(self.manuscript.siglum)


class FamilyWitness(WitnessBase):
    family = models.ForeignKey( Family, on_delete=models.CASCADE )

    def __str__(self):
        return str(self.family)


class Collection(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def witnessess_no_correctors(self):
        witnesses = WitnessBase.objects.filter(attestation__reading__location__collection=self, attestation__corrector=None)
        # For some reason this query set is not unique
        witnesses = list(set(witnesses))
        return witnesses

    def locations(self):
        return self.locationbase_set.all()

    def write_nexus(self, filename, witnesses=None, locations=None):
        if witnesses is None:
            witnesses = self.witnessess_no_correctors()

        if locations is None:
            locations = self.locations()

        state_counts = np.asarray([location.reading_set.count() for location in locations])
        max_states = state_counts.max()

        with open(filename, "w") as file:
            file.write("#NEXUS\n")
            file.write("begin data;\n")
            file.write("\tdimensions ntax=%d nchar=%d;\n" % (len(witnesses), locations.count()))
            file.write("\tformat datatype=Standard interleave=no gap=- missing=? ")    
            symbols =  "0123456789"
            max_states = len(symbols)
            file.write('symbols="')
            for x in range(max_states):
                file.write( "%s" % symbols[x] )
            file.write("\";\n")
            
            file.write('\tCHARSTATELABELS\n')
            index = 0
            for index, state_count in enumerate(state_counts):        
                labels = ['State%d' % int(state) for state in range(state_count)]
                file.write("\t\t%d  Character%d / %s,\n" %( index+1, index+1, ". ".join( labels ) ) )
                index += 1
            file.write("\t;\n")

            # Work out the longest length of a siglum for a witness to format the matrix
            max_siglum_length = 0
            for witness in witnesses:
                siglum = str(witness)
                if len(siglum) > max_siglum_length:
                    max_siglum_length = len(siglum)
            
            margin = max_siglum_length + 5

            # Write the alignment matrix
            file.write("\tmatrix\n")
            for witness in witnesses:
                siglum = str(witness)

                # Write the siglum and leave a gap for the margin
                file.write("\t%s%s" % (siglum, " "*(margin-len(siglum)) ))

                for location in locations:
                    attestations = Attestation.objects.filter( witness=witness, reading__location=location, corrector=None )
                    
                    if attestations.count() == 0 or (str(witness) == "arb" and location.id < 47):
                        labels = ["?"]
                    else:
                        labels = [location.label_for_reading(attestation.reading) for attestation in attestations]

                    if len(labels) == 1:
                        file.write(labels[0])
                    else:
                        file.write("{%s}"%("".join(labels)) )

                file.write("\n")

            file.write('\t;\n')
            file.write('end;\n')


    def write_beast_patch( self, beast_patch_filename, locations=None, atext_probability=0.6, only_category_A=False, clock_name="StrictClock" ):
        collection = self
        if locations is None:
            locations = collection.locations()
                
        family = str(collection)

        index = 0
        with open(beast_patch_filename, "w") as file:
            file.write(f'<!-- START PATCH -->\n')
            for location in locations:
                index += 1 # Beast starts at 1

                rate_symbols = []
                readings = list(location.reading_set.all())
                if len(readings) <= 1:
                    continue
                    raise Exception(f"Only 1 reading in location {location}")
                    
                print(readings, 'readings')
                state_count = len(readings)
                for start_reading_index, start_reading in enumerate(readings):
                    for end_reading_index, end_reading in enumerate(readings):
                        if start_reading == end_reading:
                            continue

                        if start_reading == location.byz:
                            rate_symbol = "FROM_BYZ_RATE"
                        elif end_reading == location.byz:
                            rate_symbol = "TO_BYZ_RATE"                            
                        else:
                            rate_symbol = "DEFAULT_RATE"                                                        

                        rate_symbols.append( rate_symbol )

                freq = 1.0/state_count
                freq_string = " ".join([str(freq) for _ in range(state_count)])

                file.write(f'<distribution id="morphTreeLikelihood.{family}.character{index}" spec="TreeLikelihood" useAmbiguities="true" branchRateModel="@{clock_name}" tree="@Tree.t:{family}">\n')
                file.write(f'\t<data\n')
                file.write(f'\t\t\tid="filter{index}"\n')
                file.write(f'\t\t\tspec="FilteredAlignment"\n')
                file.write(f'\t\t\tdata="@{family}"\n')
                file.write(f'\t\t\tfilter="{index}">\n')
                                            
                file.write(f'\t\t<userDataType id="morphDataType.{family}.character{index}" spec="beast.evolution.datatype.StandardData" ambiguities="REPLACE_AMBIGUTIIES_HERE" nrOfStates="{state_count}"/>\n')
                                        
                file.write(f'\t</data>\n')
                                    
                file.write(f'\t<siteModel id="morphSiteModel.s:{family}.character{index}" spec="SiteModel">\n')
                                            
                file.write(f'\t\t<parameter id="mutationRate.s:.{family}.character{index}" spec="parameter.RealParameter" estimate="false" name="mutationRate">1.0</parameter>\n')
                                            
                file.write(f'\t\t<parameter id="gammaShape.s:.{family}.character{index}" spec="parameter.RealParameter" estimate="false" name="shape">1.0</parameter>\n')
                                            
                #file.write(f'\t\t<substModel id="LewisMK.s:.{family}.character{index}" spec="LewisMK" datatype="@morphDataType.{family}.character{index}"/>\n')
                file.write(f'\t\t<substModel id="SubstModel.{family}.character{index}" spec="GeneralSubstitutionModel">\n')
                
                
                file.write(f'\t\t\t<frequencies id="freqs.{family}.character{index}" spec="Frequencies">\n')
                file.write(f'\t\t\t\t<frequencies id="frequencies.{family}.character{index}" spec="parameter.RealParameter" value="{freq_string}" estimate="false"/>\n')
                file.write(f'\t\t\t</frequencies>\n')
                
                
                file.write(f'\t\t\t<parameter id="rates.{family}.character{index}" spec="parameter.CompoundValuable" name="rates">\n')
                for rate_symbol in rate_symbols:
                    file.write(f'\t\t\t\t<var idref="{rate_symbol}"/>\n')
                    #file.write(f'\t\t\t\t<var spec="parameter.RealParameter" characterName="Character391" codeMap="0=0, 1=1, ? =0 1 " states="2" value="State0., State1"/>\n')    
                file.write(f'\t\t\t</parameter>\n')
                file.write(f'\t\t</substModel>\n')

                #<rates id='relativeGeoRates' spec='parameter.RealParameter' value='1.' dimension='3'/>
                
                                        
                file.write(f'\t</siteModel>\n')

                if location.ausgangstext and (only_category_A or location.category == location.CategoryUBS.A):
                    not_atext_probability = (1.0 - root_probability)/(location.reading_set.count() - 1)
                    
                    not_atext_probability_str = str(not_atext_probability)
                    rootfreqs = [str(atext_probability) if location.ausgangstext == reading else not_atext_probability_str for reading in location.reading_set.all()]
                    rootfreq_string = " ".join(rootfreqs)
                    # print(rootfreq_string, location.reading_set.count())
                    file.write(f'\t<rootFrequencies id="rootfreqs.{family}.character{index}" spec="Frequencies">\n')
                    file.write(f'\t\t<frequencies id="rootfrequencies.{family}.character{index}" spec="parameter.RealParameter" value="{rootfreq_string}" estimate="false"/>\n')
                    file.write(f'\t</rootFrequencies>\n')

                file.write(f'</distribution>\n')
            file.write(f'<!-- END PATCH -->\n')        


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
        return self.reference()

    def reference(self, abbreviation=False):
        return self.start_verse.reference(abbreviation=abbreviation, end_verse=self.end_verse)

    class Meta:
        ordering = ['collection', 'rank']

    def next(self):
        return type(self).objects.filter(collection=self.collection, rank__gt=self.rank).first()

    def prev(self):
        return type(self).objects.filter(collection=self.collection, rank__lt=self.rank).last()

    def verses(self):
        verse_class = type(self.start_verse)
        end_verse = self.end_verse
        if not end_verse:
            end_verse = self.start_verse
        return verse_class.objects.filter(rank__gte=self.start_verse.rank, rank__lte=end_verse.rank)


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

    def label_for_reading(self, reading):
        label_number = self.reading_set.filter(id__lt=reading.id).count()
        # if not self.byz:
        #     label_number = self.reading_set.filter(id__lte=reading.id).count()
        # else:
        #     if reading == self.byz:
        #         return "0"
        
        #     label_number = self.reading_set.filter(id__lte=reading.id).exclude(id=self.byz.id).count()
        if label_number > 9:
            raise ValueError
        return str(label_number)

    def category_label(self):
        if self.category is None:
            return "–"
        return chr( ord('A') + self.category )


class Reading(models.Model):
    text = models.TextField()
    location = models.ForeignKey(LocationBase, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

    def tex(self):
        """ Returns a string suitable for formatting in TeX. """
        return re.sub(r"<i>(.*?)</i>", "\\\\textit{\\1}", self.text)

    def attestations(self):
        return Attestation.objects.filter(reading=self).all()

    def witnesses_sigla(self):
        return " ".join( [attestation.witness_siglum() for attestation in self.attestations()] )    


class Attestation(models.Model):
    witness = models.ForeignKey( WitnessBase, on_delete=models.CASCADE )
    reading = models.ForeignKey( Reading, on_delete=models.CASCADE )
    text = models.TextField( default=None, null=True, blank=True )
    info = models.TextField( default=None, null=True, blank=True )
    corrector = models.PositiveIntegerField( default=None, null=True, blank=True )

    def witness_siglum(self):
        witness_siglum = str(self.witness)
        if self.corrector is None:
            return witness_siglum
        if self.corrector == 0:
            return f"{witness_siglum}-*"
        return f"{witness_siglum}-{self.corrector}"


class Contra(models.Model):
    """ A manuscript in a family witness that is contrary to the family text. """
    attestation = models.ForeignKey( Attestation, on_delete=models.CASCADE )
    manuscript = models.ForeignKey( Manuscript, on_delete=models.CASCADE )
    verse = models.ForeignKey( Verse, on_delete=models.CASCADE )


class ExtantVerse(models.Model):
    """ A verse where a witness is extant. """
    witness = models.ForeignKey( WitnessBase, on_delete=models.CASCADE )
    verse = models.ForeignKey( Verse, on_delete=models.CASCADE )

    def __str__(self):
        return f"{self.witness} {self.verse}"