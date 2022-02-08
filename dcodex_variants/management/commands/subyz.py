from django.core.management.base import BaseCommand, CommandError
from dcodex_variants.models import *
from lxml import etree
from pathlib import Path


def atext_probabilities_fixed(count, atext_probability=0.8):
    if count <= 1:
        raise Exception(f"count = {count}")
        return 1.0, 0.0
    not_atext_probability = (1.0 - atext_probability)/(count - 1)

    return atext_probability, not_atext_probability

def atext_probabilities_weight(count, weight=3.0):
    atext_probability = weight * 1.0/(count - 1 + weight)
    not_atext_probability = (1.0 - atext_probability)/(count - 1)

    return atext_probability, not_atext_probability


class Command(BaseCommand):
    help = "Modifies a BEAST2 xml file to use the Subyz substitution model."

    def add_arguments(self, parser):
        parser.add_argument(
            "collection", type=str, help="The name of the collection that is in the XML file."
        )
        parser.add_argument(
            "xml",
            type=str,
            help="The XML file to augment with the Subyz model.",
        )
        parser.add_argument(
            "output",
            type=str,
            help="The path where the output should be saved.",
        )

    def handle(self, *args, **options):
        collection = Collection.objects.get(name=options["collection"])
        locations = collection.locations()


        TO_BYZ_RATE = "TO_BYZ_RATE"
        FROM_BYZ_RATE = "FROM_BYZ_RATE"
        DEFAULT_RATE = "DEFAULT_RATE"

        print(collection)

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.parse(options["xml"], parser=parser)

        ###############################
        ####        Add Rates
        ###############################
        state = root.find(".//state")

        # <!-- START PATCH 1 -->
        # <parameter id="TO_BYZ_RATE" spec="parameter.RealParameter"  name="stateNode" lower="0.0" upper="Infinity" estimate='true'>1.0</parameter>
        # <parameter id="FROM_BYZ_RATE" spec="parameter.RealParameter"  name="stateNode" lower="0.0" upper="Infinity" estimate='true'>1.0</parameter>
        # <parameter id="DEFAULT_RATE" spec="parameter.RealParameter"  name="stateNode" lower="0.0" upper="Infinity" estimate='false'>1.0</parameter>
        # <!-- END PATCH 1 -->                            

        state.append( etree.Comment(' START PATCH RATE ') )
        to_byz_rate = etree.Element("parameter", id=TO_BYZ_RATE, spec="parameter.RealParameter",  name="stateNode", lower="0.0", upper="Infinity", estimate='true')
        to_byz_rate.text = "1.0"
        state.append( to_byz_rate )

        from_byz_rate = etree.Element("parameter", id=FROM_BYZ_RATE, spec="parameter.RealParameter",  name="stateNode", lower="0.0", upper="Infinity", estimate='true')
        from_byz_rate.text = "1.0"
        state.append( from_byz_rate )

        from_byz_rate = etree.Element("parameter", id=DEFAULT_RATE, spec="parameter.RealParameter",  name="stateNode", lower="0.0", upper="Infinity", estimate='false')
        from_byz_rate.text = "1.0"
        state.append( from_byz_rate )

        state.append( etree.Comment(' END PATCH RATE ') )


        ###############################
        ####        Add Likelihood
        ###############################
        likelihood = root.find(".//distribution[@id='likelihood']")
        clock = likelihood.find(".//branchRateModel")

        # Clear old likelihoods
        for child in list(likelihood):
            likelihood.remove(child)
            likelihood_log = root.find(f".//log[@idref='{child.get('id')}']")
            if likelihood_log is not None:
                likelihood_log.getparent().remove(likelihood_log)

        tree = root.find(".//tree")
        tree_id = tree.get('id')
        data = root.find(".//data")
        data_id = data.get('id')

        likelihood.append( etree.Comment(' START PATCH LIKELIHOOD ') )
        index = 0
        for location in locations:
                index += 1 # Beast starts at 1

                rate_symbols = []
                readings = list(location.reading_set.all())
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

                distribution_attrs = dict(
                    id=f"morphTreeLikelihood.character{index}", 
                    useAmbiguities="true", 
                    spec="TreeLikelihood",  
                    tree=f"@{tree_id}"
                )
                if index != 1:
                    distribution_attrs["branchRateModel"] = f"@{clock.attrib['id']}"

                distribution = etree.Element(
                    "distribution", 
                    **distribution_attrs,
                )
                data = etree.SubElement(
                    distribution,
                    "data", 
                    id=f"filter{index}", 
                    spec="FilteredAlignment",  
                    data=f"@{data_id}",
                    filter=str(index),
                )

                data.append( etree.Element(
                    "userDataType",
                    id=f"morphDataType.character{index}",
                    spec="beast.evolution.datatype.StandardData",
                    ambiguities="", # Confirm this
                    nrOfStates=str(state_count),
                ))

                site_model = etree.SubElement(
                    distribution,
                    "siteModel", 
                    id=f"morphSiteModel.character{index}", 
                    spec="SiteModel",  
                )

                etree.SubElement(
                    site_model, 
                    "parameter",
                    id=f"mutationRate.character{index}",
                    spec="parameter.RealParameter",
                    estimate="false",
                    name="mutationRate",
                ).text = "1.0"
                etree.SubElement(
                    site_model, 
                    "parameter",
                    id=f"gammaShape.character{index}",
                    spec="parameter.RealParameter",
                    estimate="false",
                    name="shape",
                ).text = "1.0"

                substitution_model = etree.SubElement(
                    site_model,
                    "substModel",
                    id=f"SubstModel.character{index}",
                    spec="GeneralSubstitutionModel",
                )

                frequencies = etree.SubElement(
                    substitution_model,
                    "frequencies",
                    id=f"freqs.character{index}",
                    spec="Frequencies",
                )                
                etree.SubElement(
                    frequencies,
                    "frequencies",
                    id=f"frequencies.character{index}",
                    spec="parameter.RealParameter",
                    value=freq_string,
                    estimate="false",
                )                

                rates = etree.SubElement(
                    substitution_model,
                    "parameter",
                    id=f"rates.character{index}",
                    spec="parameter.CompoundValuable",
                    name="rates",
                )                
                for rate_symbol in rate_symbols:
                    etree.SubElement(
                        rates,
                        "var",
                        idref=rate_symbol,
                    )

                if location.ausgangstext:
                    print(location)
                    ausgangstext_probability, not_ausgangstext_probability = atext_probabilities_fixed(location.reading_set.count(), 0.8)                    
                    rootfreqs = [str(ausgangstext_probability) if location.ausgangstext == reading else str(not_ausgangstext_probability) for reading in location.reading_set.all()]
                    rootfreq_string = " ".join(rootfreqs)
                    root_frequencies = etree.SubElement(
                        distribution,
                        "rootFrequencies",
                        id=f"rootfreqs.character{index}",
                        spec="Frequencies",
                    )
                    etree.SubElement(
                        root_frequencies,
                        "frequencies",
                        id=f"rootfrequencies.character{index}",
                        spec="parameter.RealParameter",
                        value=rootfreq_string,
                        estimate="false", # This could be good to estimate
                    )

                if index == 1:
                    distribution.append( clock )

                likelihood.append(distribution)
        likelihood.append( etree.Comment(' END PATCH LIKELIHOOD ') )

                                    
        #         file.write(f'\t<siteModel id="morphSiteModel.s:{family}.character{index}" spec="SiteModel">\n')
                                            
        #         file.write(f'\t\t<parameter id="mutationRate.s:.{family}.character{index}" spec="parameter.RealParameter" estimate="false" name="mutationRate">1.0</parameter>\n')
                                            
        #         file.write(f'\t\t<parameter id="gammaShape.s:.{family}.character{index}" spec="parameter.RealParameter" estimate="false" name="shape">1.0</parameter>\n')
                                            
        #         file.write(f'\t\t<substModel id="SubstModel.{family}.character{index}" spec="GeneralSubstitutionModel">\n')
                
                
        #         file.write(f'\t\t\t<frequencies id="freqs.{family}.character{index}" spec="Frequencies">\n')
        #         file.write(f'\t\t\t\t<frequencies id="frequencies.{family}.character{index}" spec="parameter.RealParameter" value="{freq_string}" estimate="false"/>\n')
        #         file.write(f'\t\t\t</frequencies>\n')
                
                
        #         file.write(f'\t\t\t<parameter id="rates.{family}.character{index}" spec="parameter.CompoundValuable" name="rates">\n')
        #         for rate_symbol in rate_symbols:
        #             file.write(f'\t\t\t\t<var idref="{rate_symbol}"/>\n')
        #             #file.write(f'\t\t\t\t<var spec="parameter.RealParameter" characterName="Character391" codeMap="0=0, 1=1, ? =0 1 " states="2" value="State0., State1"/>\n')    
        #         file.write(f'\t\t\t</parameter>\n')
        #         file.write(f'\t\t</substModel>\n')

        #         #<rates id='relativeGeoRates' spec='parameter.RealParameter' value='1.' dimension='3'/>
                
                                        
        #         file.write(f'\t</siteModel>\n')

        #         if location.category == location.CategoryUBS.A and location.ausgangstext:
        #             category_A_probability, not_category_A_probability = probabilities_80(location.reading_set.count())
                    
        #             not_category_A_probability_str = str(not_category_A_probability)
        #             rootfreqs = [str(category_A_probability) if location.ausgangstext == reading else not_category_A_probability_str for reading in location.reading_set.all()]
        #             rootfreq_string = " ".join(rootfreqs)
        #             # print(rootfreq_string, location.reading_set.count())
        #             file.write(f'\t<rootFrequencies id="rootfreqs.{family}.character{index}" spec="Frequencies">\n')
        #             file.write(f'\t\t<frequencies id="rootfrequencies.{family}.character{index}" spec="parameter.RealParameter" value="{rootfreq_string}" estimate="false"/>\n')
        #             file.write(f'\t</rootFrequencies>\n')

        #         file.write(f'</distribution>\n')
        # file.write(f'<!-- END PATCH -->\n')






# <distribution id="morphTreeLikelihood.Mark.character1" spec="TreeLikelihood" tree="@Tree.t:Mark">
# 	<data
# 			id="filter1"
# 			spec="FilteredAlignment"
# 			data="@Mark"
# 			filter="1">
# 		<userDataType id="morphDataType.Mark.character1" spec="beast.evolution.datatype.StandardData" ambiguities="" nrOfStates="5"/>
# 	</data>
# 	<siteModel id="morphSiteModel.s:Mark.character1" spec="SiteModel">
# 		<parameter id="mutationRate.s:.Mark.character1" spec="parameter.RealParameter" estimate="false" name="mutationRate">1.0</parameter>
# 		<parameter id="gammaShape.s:.Mark.character1" spec="parameter.RealParameter" estimate="false" name="shape">1.0</parameter>
# 		<substModel id="SubstModel.Mark.character1" spec="GeneralSubstitutionModel">
# 			<frequencies id="freqs.Mark.character1" spec="Frequencies">
# 				<frequencies id="frequencies.Mark.character1" spec="parameter.RealParameter" value="0.2 0.2 0.2 0.2 0.2" estimate="false"/>
# 			</frequencies>
# 			<parameter id="rates.Mark.character1" spec="parameter.CompoundValuable" name="rates">
# 				<var idref="TO_BYZ_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="FROM_BYZ_RATE"/>
# 				<var idref="FROM_BYZ_RATE"/>
# 				<var idref="FROM_BYZ_RATE"/>
# 				<var idref="FROM_BYZ_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="TO_BYZ_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="TO_BYZ_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="TO_BYZ_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 				<var idref="DEFAULT_RATE"/>
# 			</parameter>
# 		</substModel>
# 	</siteModel>
# 	<branchRateModel id="RandomLocalClock.c:Mark" spec="beast.evolution.branchratemodel.RandomLocalClockModel" clock.rate="@meanClockRate.c:Mark" indicators="@Indicators.c:Mark" rates="@clockrates.c:Mark" tree="@Tree.t:Mark"/>
# </distribution>



            # <distribution id="likelihood" spec="util.CompoundDistribution" useThreads="true">
            #     <distribution id="morphTreeLikelihood.1Co2" spec="TreeLikelihood" data="@1Co2" tree="@Tree.t:1Co">
            #         <siteModel id="morphSiteModel.s:1Co2" spec="SiteModel">
            #             <parameter id="mutationRate.s:1Co2" spec="parameter.RealParameter" estimate="false" name="mutationRate">1.0</parameter>
            #             <parameter id="gammaShape.s:1Co2" spec="parameter.RealParameter" estimate="false" name="shape">1.0</parameter>
            #             <substModel id="LewisMK.s:1Co2" spec="LewisMK" datatype="@morphDataType.1Co2" />
            #         </siteModel>
            #         <branchRateModel id="StrictClock.c:1Co" spec="beast.evolution.branchratemodel.StrictClockModel" clock.rate="@clockRate.c:1Co" />
            #     </distribution>
            #     <distribution id="morphTreeLikelihood.1Co3" spec="TreeLikelihood" branchRateModel="@StrictClock.c:1Co" tree="@Tree.t:1Co">
            #         <data id="1Co3" spec="FilteredAlignment" data="@1Co" filter="7,16-17,43,56,60,83,88,94,97,100,111,120-121,123-124,127,131,139,144,150,155,157,160,165-166,169,179,182,191,193,203,207,216-217,225,227,232,235,238-239,244,248-249,282,287,290,296,306,308,310,315,324,341,363,366-367,381,396,425,431,438-439,444-446,453,455">
            #             <userDataType id="morphDataType.1Co3" spec="beast.evolution.datatype.StandardData" ambiguities="12 01 02" nrOfStates="3" />
            #         </data>
            #         <siteModel id="morphSiteModel.s:1Co3" spec="SiteModel">
            #             <parameter id="mutationRate.s:1Co3" spec="parameter.RealParameter" estimate="false" name="mutationRate">1.0</parameter>
            #             <parameter id="gammaShape.s:1Co3" spec="parameter.RealParameter" estimate="false" name="shape">1.0</parameter>
            #             <substModel id="LewisMK.s:1Co3" spec="LewisMK" datatype="@morphDataType.1Co3" />
            #         </siteModel>
            #     </distribution>

        # TODO


        ###############################
        ####        Add Operator
        ###############################
        operator = root.find(".//operator")

        # <!-- Start Patch -->
        # <operator id='Scaler.TO_BYZ_RATE' spec='ScaleOperator' scaleFactor="0.5" weight="1" parameter="@TO_BYZ_RATE"/>
        # <operator id='Scaler.FROM_BYZ_RATE' spec='ScaleOperator' scaleFactor="0.5" weight="1" parameter="@FROM_BYZ_RATE"/>        
        # <!-- End Patch -->
        operator.addprevious( etree.Comment(' START PATCH OPERATOR ') )
        operator.addprevious(
            etree.Element("operator", id=f'Scaler.{TO_BYZ_RATE}', spec='ScaleOperator', scaleFactor="0.5", weight="1", parameter=f"@{TO_BYZ_RATE}")
        )
        operator.addprevious(
            etree.Element("operator", id=f'Scaler.{FROM_BYZ_RATE}', spec='ScaleOperator', scaleFactor="0.5", weight="1", parameter=f"@{FROM_BYZ_RATE}")
        )
        operator.addprevious( etree.Comment(' END PATCH OPERATOR ') )


        ###############################
        ####        Logger
        ###############################
        # <!-- Start Patch -->        
        # <log idref="TO_BYZ_RATE"/>
        # <log idref="FROM_BYZ_RATE"/>
        # <!-- End Patch -->            

        # logger = root.find(".//logger[id='tracelog']")
        logger = root.find(".//logger")
        logger.append( etree.Comment(' START PATCH LOGGER ') )
        logger.append( etree.Element("log", idref=TO_BYZ_RATE) )
        logger.append( etree.Element("log", idref=FROM_BYZ_RATE) )
        logger.append( etree.Comment(' END PATCH LOGGER ') )

        ###############################
        ####        Output
        ###############################
        output_path = Path(options["output"])
        output_path.parent.mkdir(exist_ok=True, parents=True)
        root.write(str(output_path), pretty_print=True)
        