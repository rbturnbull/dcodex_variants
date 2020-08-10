import sys
import re
from bs4 import BeautifulSoup
import regex
from collections import Counter
from dcodex_bible.models import BibleVerse
from dcodex_variants.models import *
import os

greek_reading_pattern = "([—…ʼ·:-]*\p{IsGreek}+|(<i>.*?</i>)+|(\(<i>see.*?<\/i>.*?\))*)((\(<i>.*?<\/i>.*?\))*(<i>.*?<\/i>)*[ ̓\.\;\, ·:-]*\p{IsGreek}*[—…ʼ\=·:\/-]*)*"


def make_witness(name, corrector = "", info = ""):
    if name[-1] == "*":
        corrector = "*"
        name = name[:-1]

    if name[-1] == "?":
        info = "Uncertain. "+info
        name = name[:-1]

    if " " in name:
        print("Illegal name:", name)
        sys.exit()    
    if name == 'א':
        name = "ℵ"
    if name == "ℵ":
        name = "01" # The symbol "ℵ" can break outputs
    
    if name[-1] in ['.',',']:
        name = name[:-1]
            
    sigla = { "Θ" : "038", "Λ" : "039", "Δ" : "037", "Γ" : "036", "Ξ" : "040", "Π" : "041", "Σ" : "042", "Ψ" : "044" }
    if name in sigla.keys():
        name = sigla[name]  

    if name[0] == "_":
        raise TypeError("Illegal name: '%s'" % name)

    
    if name in ["</sup>", "<i>see</i>", "syr__with", "…", "P46vid", "P11vid", "P46</sup>", 'class="s1">𝔓</span>', 't</sup>', 'terra', '/sup>', 'mg','', 'cop__', 'some',
            "P𝔓46", "A*", '42/63', 'P46*', 'Greek', 'o', 'of', 'and', '<i>l</i>', 'αὐτοῦ','<i>compare','̓Ιησοῦς', 'τῷ', '<i>at', 'Constitutions', '=', 'cop__samss','?</sup>',
            'Χριστὸς', 'παρθένος', 'ἄγαμος', '(Cyril', 'cop__(bo', 'it__b)', 'ὁ', 'ὄχλους', 'τοὺς', 'λοιμοί', '(pal)</sup>', '<sup>vid</sup>', '-', 'ℵ*,', 'et', 'syr__1', 'syr__2', '<span', 
            'coppbo', 'αὐτῷ', '7:53–8:11', '<sup>c</sup>', 'pal', 'it__','ach2', '1:71',
            None
            
            ] or "<i>" in name or '(' in name or ')' in name or ',' in name or '<' in name or ':' in name:

        raise TypeError("Illegal name: '%s'" % name)
        sys.exit()

    witness, _ = SiglumWitness.objects.update_or_create(siglum=name)
    return witness, corrector, info


def add_attestation( reading, name, corrector = "", info = "", subvariant= ""):
    witness, corrector, info = make_witness( name, corrector, info )

    if corrector == "*":
        corrector = 0
    elif corrector == "c":
        corrector = 1
    elif corrector == "":
        corrector = None

    Attestation.objects.update_or_create( reading=reading, witness=witness, corrector=corrector, defaults={
        'info':info, 
        'text':subvariant,
    })

    if witness.siglum == "Byz":
        reading.location.byz = reading
        reading.location.save()

        


def pop_witnesses_class( current_reading, witnesses_string, members, class_name, general_subvariant="" ):
    print("Pop class:", class_name, ':', witnesses_string)
    parentheses = False
    close_parentheses = False
    pattern = class_name+"<sup>(.+?)<\/sup>"
    m = re.search( pattern, witnesses_string )
    if m:
        members_string = m.group(1).replace( ",", " ")
        
        for member_name in members_string.split():
            subvariant = general_subvariant
            corrector = ""

            if member_name[0] == "(":
                member_name = member_name[1:]
                subvariant = "Minor Difference"
                parentheses = True
                
            if member_name[-1] == ")":
                member_name = member_name[:-1]
                close_parentheses = True
                
            if parentheses:
                subvariant = "Minor Difference"
            
            info = ""
            if "|" in member_name:
                index = member_name.index("|")
                info = member_name[index+1:]                
                member_name = member_name[:index]
                
            if class_name == "syr":
                if member_name == "hmetobelos":
                    info += " a Syriac reading in the text enclosed between an asterisk and a metobelos"
                    member_name = "h"
                if member_name == "hmg":
                    info += " a Syriac variant reading in the margin"
                    member_name = "h"
                if member_name == "hgr":
                    info += " a Greek qualification in the margin for a Syriac reading"
                    member_name = "h"

            
            if member_name[-3:] == "vid":
                member_name = member_name[:-3]
                info += " vid"

            if len(member_name) > 1 and member_name[-1:] == "c":
                member_name = member_name[:-1]
                corrector = "c"
                
            if member_name[-1:] == "*":
                corrector = "*"
                member_name = member_name[:-1]
                

            info = info.strip()
            
            print(f"member_name: '{member_name}'")
            
            if class_name == "𝔓":
                #member_name = class_name + member_name
                member_name = "P" + member_name # Make it a normal P because it is inline
            else:
                member_name = "%s__%s" % (class_name, member_name)
            
            if member_name.strip() == ",":
                continue

            witness = add_attestation(current_reading, member_name, subvariant=subvariant, info=info, corrector=corrector)
#            print(witness)
            
            if close_parentheses:
                close_parentheses = False
                parentheses = False
            
            members += [witness]
        witnesses_string = re.sub( pattern, "", witnesses_string )
        return witnesses_string, members

    return witnesses_string, members

def pop_all_classes( current_reading, text, witnesses, subvariant = "" ):

    text, witnesses = pop_witnesses_class( current_reading, text, witnesses, "𝔓", subvariant )
    text, witnesses = pop_witnesses_class( current_reading, text, witnesses, "it", subvariant )
    text, witnesses = pop_witnesses_class( current_reading, text, witnesses, "cop", subvariant )
    text, witnesses = pop_witnesses_class( current_reading, text, witnesses, "syr", subvariant )
    return text, witnesses
    
def deal_with_sups( current_reading, text, witnesses, subvariant = "" ):
    # First get witnesses with superscripted text
    superscripted_pattern = "([^\s]+)<sup>(.+?)<\/sup>"
    for superscripted in re.findall( superscripted_pattern, text ):
        corrector = ""
        name = superscripted[0]
        if name[-1] == "*":
            corrector = "*"
            name = name[:-1]
    
        print("superscript:", superscripted)
        
        superscript = superscripted[1].strip(", ")
        if superscript.isdigit() or superscript == 'c':
            if corrector == "*":
                add_attestation( current_reading, name, corrector=corrector, subvariant=subvariant ) # e.g. D*<sup>, 2</sup>                

            add_attestation( current_reading, name, corrector=superscript, subvariant=subvariant )
        else:
            add_attestation( current_reading, name, info=superscript, subvariant=subvariant, corrector=corrector )
    text = re.sub( superscripted_pattern, "", text )
    return text, witnesses    
    
def split_witnesses( current_reading, text, subvariant = "" ):
    text = text.replace( ";", "" )
    witnesses = []
    
    text, witnesses = pop_all_classes( current_reading, text, witnesses, subvariant )
    text, witnesses = deal_with_sups( current_reading, text, witnesses, subvariant )
    
    print('text split_witnesses', text)    
    for name in text.split():
        corrector = ""
        info = ""
        if name[-1] == "*":
            corrector = "*"
            name = name[:-1]

        if name[-1] == "?":
            info = "Uncertain"
            name = name[:-1]
            
            
        add_attestation( current_reading, name, subvariant=subvariant, corrector=corrector, info=info )
    return witnesses

def strip_commas_from_sups( text ):
    start = 0
    new_string = ""
    while True :
        left = text[start:].find( "<sup>" )
        if left < 0:
            break
        right = text[start+left:].find( "</sup>" )
        if right < 0:
            break
        
        new_string += text[start:start+left] + text[start+left:start+left+right].replace( ",", "" )
        print(left, right)

        start += left+right
    return new_string + text[start:]

def parse_witnesses( current_reading, witnesses_string, members ):
    witnesses_string = witnesses_string.replace( ";", "" )
    
    while witnesses_string:
        witnesses_string = witnesses_string.strip()
        first_space = witnesses_string.find( " " )
        first_sup = witnesses_string.find( "<sup>" )
        first_bracket = witnesses_string.find( "(" )
#        print('while witnesses_string:', witnesses_string)

        if first_space >= 0 and ( first_space < first_sup or first_sup < 0 ) and ( first_space < first_bracket or first_bracket < 0 ):        # Check if space
            name = witnesses_string[:first_space]
            print('name:', name)
            if name != ",":
                add_attestation( current_reading, name )
            witnesses_string = witnesses_string[first_space+1:]
        elif first_sup >= 0 and ( first_sup < first_bracket or first_bracket < 0 ): # Sup
            close_sup = witnesses_string.find( "</sup>" )
            sups_string = witnesses_string[:close_sup+6]
            sups_string, members = pop_all_classes( current_reading, sups_string, members )
            sups_string, members = deal_with_sups( current_reading, sups_string, members )
            witnesses_string = witnesses_string[close_sup+6:]
        elif first_bracket >= 0: # next marker is a bracket
            right_bracket = witnesses_string.rfind(")")
            left_bracket = first_bracket
            nested = 0
            for char_index in range( left_bracket + 1, right_bracket ):
                #print(witnesses_string[char_index], nested)
                if witnesses_string[char_index] == "(":
                    nested += 1
    
                if witnesses_string[char_index] == ")":
                    if nested == 0:
                        right_bracket = char_index
                        break
                    nested -= 1
        
            # Process the inner text
            text = witnesses_string[left_bracket+1:right_bracket].strip()
        
            print("Inner text:", text )
            
            text = strip_commas_from_sups( text )
            print("Inner text - no commas between sups", text )

            components = text.split( "," )
            for component in components:
            
                m = regex.search( greek_reading_pattern + "$", component )
                if m and len(m.group(0)) > 0:
                    subvariant = m.group(0)
                    component = component[:m.span()[0]]
                    print('subvariant right:', subvariant, m)
            
                else:
                    m = regex.search( "^"+greek_reading_pattern, component )
                    if m and len(m.group(0)) > 0:
                        subvariant = m.group(0)
                        component = component[m.span()[1]:]
                        print('subvariant left:', subvariant)
                
                    else:
                        subvariant = "Minor Difference"            
        
                print('subvariant:', subvariant)
        
                members += split_witnesses( current_reading, component, subvariant )    # This should be a call to this function    
        
            witnesses_string = witnesses_string[:left_bracket] + witnesses_string[right_bracket+1:]        
        else: # End of line
            print( witnesses_string )
            print(first_space)
            print(first_sup)
            print(first_bracket)
            if witnesses_string:
                print('www:', witnesses_string)
                add_attestation( current_reading, witnesses_string )                
            witnesses_string = ""
            break

    return "", members
            
            


def pop_brackets( witnesses_string, members ):
    print( 'pop_brackets:', witnesses_string )
    raise
    left_bracket = witnesses_string.find("(")
    right_bracket = witnesses_string.rfind(")")
    # Find Matching Brackets
    while 0 <= left_bracket < right_bracket:
        
        # Check if in superscript - this is a big hack
        print(witnesses_string[:left_bracket].rfind( "<sup>" ))
        print("</sup>", witnesses_string[:left_bracket].rfind( "</sup>" ))
        if witnesses_string[:left_bracket].rfind( "<sup>" ) > witnesses_string[:left_bracket].rfind( "</sup>" ):
            print("sup outside brackets:", witnesses_string )
            print("string:", witnesses_string[:left_bracket] )
            print("left:", witnesses_string[:left_bracket].rfind( "<sup>" ) )
            print("right:", witnesses_string[:left_bracket].rfind( "</sup>" ) )
            witnesses_string, members = pop_all_classes(current_reading, witnesses_string, members)
            witnesses_string, members = deal_with_sups( current_reading, witnesses_string, members )
 
            print("fixed?:", witnesses_string )            
            left_bracket = witnesses_string.find("(")
            right_bracket = witnesses_string.rfind(")")
            continue
            
        
        
        nested = 0
        for char_index in range( left_bracket + 1, right_bracket ):
            #print(witnesses_string[char_index], nested)
            if witnesses_string[char_index] == "(":
                nested += 1
    
            if witnesses_string[char_index] == ")":
                if nested == 0:
                    right_bracket = char_index
                    break
                nested -= 1
        
        # Process the inner text
        text = witnesses_string[left_bracket+1:right_bracket].strip()
        
        print("Inner text:", text )
        
        components = text.split( "," )
        for component in components:
            m = regex.search( greek_reading_pattern + "$", component )
            if m and len(m.group(0)) > 0:
                subvariant = m.group(0)
                component = text[:m.span()[0]]
                print('subvariant right:', subvariant, m)
            
            else:
                m = regex.search( "^"+greek_reading_pattern, component )
                if m and len(m.group(0)) > 0:
                    subvariant = m.group(0)
                    component = text[m.span()[1]:]
                    print('subvariant left:', subvariant)
                
                else:
                    subvariant = "Minor Difference"            
        
            print('subvariant:', subvariant)
        
            members += split_witnesses( component, subvariant )        
        
        witnesses_string = witnesses_string[:left_bracket] + witnesses_string[right_bracket+1:]
    
        left_bracket = witnesses_string.find("(")
        right_bracket = witnesses_string.rfind(")")
    return witnesses_string, members
    

def run(*args):       
    if len(args) == 0:
        print("Usage: --script-args UBS_HTML_FILE")
        return

    ubs_html_file = args[0]

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
                    reading = re.sub( ".*}", "", reading ).replace("</p>","").strip()
                    print("raw", reading.strip())
                    if len(reading) == 0:
                        continue
                    
                    reading = re.sub( r"<i>l</i> ", r"𝑙", reading )
                    
                    m = regex.match( greek_reading_pattern, reading )
                    if not m:
                        m = regex.match( "<i>.*?<\/i>", reading )
                    
                    
                    if m:
                        reading_text = m.group(0).strip()
                        if len(reading_text) == 0:
                            print("Reading length 0")
                            print("Failure!")
                            sys.exit()
                        current_reading, _ = Reading.objects.update_or_create( text=reading_text, location=current_location )
                        if current_location.ausgangstext is None:
                            current_location.ausgangstext = current_reading
                            current_location.save()
                    
                        print('reading:\t', m.group(0) )
    #                    print( m.span()[1] )
                        witnesses_string = reading[m.span()[1]:]
                        

                        
                        witnesses_string = witnesses_string.replace( ',</sup> <sup>ach</sup>2', ', ach2</sup>' )
                        witnesses_string = witnesses_string.replace( "bo</sup>pt<sup>,</sup>", "bo|pt, " )
                        witnesses_string = witnesses_string.replace( "bo</sup>ms<sup>)</sup>", "bo|ms</sup>)")
                        witnesses_string = witnesses_string.replace( "2<sup>nd</sup> epistle of Clement", "2nd_epistle_of_Clement")
                        witnesses_string = witnesses_string.replace( '<span class="s3">→</span>', '' )
                        
                        witnesses_string = witnesses_string.replace( "pal</sup>?", "pal|Uncertain</sup>" )
                        witnesses_string = witnesses_string.replace( "ach2</sup>?", "ach2|Uncertain</sup>" )
                        
                        witnesses_string = witnesses_string.replace( "bo</sup>?", "bo|Uncertain</sup>" )
                        
                        witnesses_string = witnesses_string.replace( "ach</sup>2?", "ach2|Uncertain</sup>" )
                        
                        witnesses_string = witnesses_string.replace( "r</sup>1<sup> vid</sup>", "r1|vid</sup>" )
                        
                        
                        witnesses_string = witnesses_string.replace( "ff</sup>2<sup>", "ff2" )
                        witnesses_string = witnesses_string.replace( "ff</sup>1<sup>", "ff1" )
                        witnesses_string = witnesses_string.replace( "g</sup>1<sup>", "g1" )
                        witnesses_string = witnesses_string.replace( "g</sup>1<sup>", "g1" )
                        witnesses_string = witnesses_string.replace( "r</sup>1<sup>vid</sup>", "r1|vid</sup>" )
                        
                        witnesses_string = witnesses_string.replace( 'r</sup>1<sup>?</sup>', 'r1|Uncertain</sup>' )
                        
                        witnesses_string = witnesses_string.replace( " r</sup>1<sup>)</sup>", " r1</sup>)" )
                        witnesses_string = witnesses_string.replace( "r</sup>1<sup>,", "r1," )
                        witnesses_string = witnesses_string.replace( " r</sup>1", " r1</sup>" )
    #                    witnesses_string = witnesses_string.replace( "</sup>ms<sup>)</sup>", "|ms</sup>)" )
                        
                        witnesses_string = witnesses_string.replace( "mg<sup> 1</sup>", "mg1" )
                        witnesses_string = witnesses_string.replace( "mg<sup> 2", "mg2<sup>" )

                        
                        witnesses_string = witnesses_string.replace( "</sup>pt<sup>)</sup>", "|pt</sup>)" )
                        
                        
    #                    witnesses_string = witnesses_string.replace( "it<sup>e</sup>", "it__e" ) # big hack
                        #witnesses_string = witnesses_string.replace( "</sup>ms<sup>)</sup>", "|ms</sup>)" ) # big hack  
                        
                                        
                        
                        
                        
                        witnesses_string = re.sub( r"<span class=\"s1\">𝔓<\/span>", r"𝔓", witnesses_string )
                        witnesses_string = re.sub( r"<span class=\"s2\">𝔓<\/span>", r"𝔓", witnesses_string )
                        witnesses_string = re.sub( r"\[(.*?)\]", r"\1", witnesses_string )
                        witnesses_string = re.sub( r"<i>l</i> ", r"𝑙", witnesses_string )
                        witnesses_string = witnesses_string.replace( "<span class=\"s1\">א</span>", "ℵ" )
                        witnesses_string = witnesses_string.replace( "<span class=\"s2\">א</span>", "ℵ" )
                        witnesses_string = witnesses_string.replace( "<i>Byz</i>", "Byz" )
                        witnesses_string = witnesses_string.replace( "<i>Lect</i>", "Lect" )
                        witnesses_string = witnesses_string.replace( "Mar cion", "Marcion" ) # Hack - why is this?

                        witnesses_string = witnesses_string.replace(' ','')                    
                        #witnesses_string = re.sub( r"<\/sup>([^\s]+?)<sup>", r"|\1", witnesses_string )
                        
                        witnesses_string = regex.sub( r"<\/sup>([^\s\p{Punct}]+)<sup>", r"|\1", witnesses_string )
                        witnesses_string = regex.sub( r"<\/sup>([^\s\p{Punct}]+)", r"|\1</sup>", witnesses_string )
                        witnesses_string = witnesses_string.replace( "</sup>, <sup>", " " )
                        witnesses_string = witnesses_string.replace( "h with</sup> *<sup>", "hmetobelos " )
                        witnesses_string = re.sub( "h with</sup>\s*\*", "hmetobelos</sup>", witnesses_string )                    
                        witnesses_string = witnesses_string.replace( "</sup>*", "*</sup>" )     
                        witnesses_string = witnesses_string.replace( "Letter of Hymenaeus", "Letter-of-Hymenaeus" )  
                        witnesses_string = witnesses_string.replace( "Greek and Latin mss", "Greek-mss Latin-mss" )                                        
                        
                        witnesses_string = witnesses_string.replace( "Apostolic Constitutions", "Apostolic-Constitutions" )                       
                        witnesses_string = witnesses_string.replace( "Latin mss", "Latin-mss" )                       
                        witnesses_string = witnesses_string.replace( "Greek mss", "Greek-mss" )   
                        witnesses_string = witnesses_string.replace( "Docetists and Naassenes<sup>acc. to Hippolytus</sup>", "Docetists<sup>acc. to Hippolytus</sup>  Naassenes<sup>acc. to Hippolytus</sup>" )   
                        witnesses_string = re.sub( r"<i>l</i><sup>AD</sup>", r"𝑙-Apostoliki-Diakonia", witnesses_string )
                        witnesses_string = re.sub( r"<i>l</i><sup>AD1/2</sup>", r"𝑙-Apostoliki-Diakonia<sup>1/2</sup>", witnesses_string )

                        witnesses_string = witnesses_string.replace( "syr</sup>?", "syr|Uncertain</sup>" )
                        witnesses_string = witnesses_string.replace( "s</sup>?", "s|Uncertain</sup>" )
                        witnesses_string = witnesses_string.replace( "1</sup>?", "1|Uncertain</sup>" )
                        witnesses_string = witnesses_string.replace( " r1</sup>)", " r1)</sup>" )

                        
                        witnesses_string = witnesses_string.replace( "<sup>bo|ms</sup>_mg", "<sup>bo|ms_mg</sup>" )
                        witnesses_string = witnesses_string.replace( "(bo|ms</sup>)", "(bo|ms)</sup>" )
                        
                        witnesses_string = witnesses_string.replace( ",|", "|" )
                                                
                        witnesses_string = re.sub(r'(\(it<sup>.*)r1\)<\/sup>', r'\1r1</sup>)', witnesses_string) # Hack for John
                        print('witnesses string:\t', witnesses_string)
                        
                        members = []
                        
                        
                        
                        witnesses_string, members = parse_witnesses( current_reading, witnesses_string, members )
                        
                        print( 'witnesses string popped:\t', witnesses_string )
    #                    print( 'members:\t', ", ".join([str(member) for member in members]) )
                        
                        #members += split_witnesses( witnesses_string )
                        for member in members:
                            if member is None:
                                print("DHFIDHFOSDHFDF")
                            else:
                                witnesses_counter.update( [member.name] )     
    #                    print( 'members:\t', ", ".join([str(member) for member in members]) )                        
                    else:
                        print("Cannot find reading from: ", reading)
                        sys.exit()
                    print('-//')


    print("Sucess!")