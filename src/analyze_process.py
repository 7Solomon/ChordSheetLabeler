import json
import re
from typing import List, Dict, Tuple

def is_chord(text: str) -> bool:
    """Check if the text is likely a chord."""
    basic_chords = {"C",  "D",  "E", "F", "G",  "A", "B", "H"}
    if len(text) > 1: 
        return len(text)<=4 and any(char in text for char in ["7", "9", "m", "M", "maj", "dim", "aug", "sus", "add", "°", "ø", "b", "#"]) # Ka ob das alle sein müssen aber why not
    return any(char.isalpha() for char in text) and text in basic_chords


def convert_chord_to_nashV(chord: str, key: str) -> str:
    """
    Convert a chord to its Nashville number system equivalent based on the key.
    This handles extended chords like F#m7, Cmaj7, B7 by focusing on the base chord.
    """
    # Load Nashville system from a JSON file or define it as a dict here
    nashville_system = json.load(open("assets/nashville_system.json"))     # HERE PATH MAYBE FOR EXE SHOULD BE CHANGED

    # Ensure the key exists in the Nashville system
    if key not in nashville_system:
        return None
        #raise ValueError(f"Key {key} not recognized in the Nashville system.")
    
    # Get the chords for the key
    chords_for_key = nashville_system[key]

    # Strip extensions from the chord (e.g., F#m7 -> F#m)
    base_chord = re.match(r"([A-G]#?m?)(.*)", chord)
    
    if not base_chord:
        return None
        #raise ValueError(f"Chord {chord} is invalid.")
    
    base_chord_name = base_chord.group(1)  # Extract the base chord (e.g., F#m)
    chord_extension = base_chord.group(2)  # Extract the extension (e.g., 7, maj7)
    # Find the chord in the key's Nashville system
    for nash_num, nash_chord in chords_for_key.items():
        # Match major and minor chords
        if (base_chord_name.endswith("m") and nash_chord.startswith(base_chord_name[:-1])):
            return f'-{nash_num}'
        if nash_chord == base_chord_name :
            return f'{nash_num}'
    
    # If the chord is not found, return an error or a default value
    return None
    #raise ValueError(f"Chord {chord} not recognized in the key of {key}.")
def process_position(x:float, start_x:float, avg_width:float, length_of_lyrics:int) -> int:
    relativ_x = x - start_x
    print(relativ_x)
    print(avg_width)
    print((relativ_x/avg_width))
    print(length_of_lyrics)
    if relativ_x > 0:
        
        pos  = int((relativ_x/avg_width) * length_of_lyrics)
        return pos
    else:
        print('DEBUG ERROR: relativ_x is negative')
        return None
    

def process_ocr_result(ocr_result: List[Tuple], key:str, name_of_part:str) -> tuple[str,str]:
    verse_data = []
    current_line = {"lyrics": "", "chords": {}}
    _chord = None
    avg_x_pos_of_chord = None
    
    for i, item in enumerate(ocr_result):
        bbox, text, _prob = item    # I think _ is prob, but not sure
        
        x = bbox[0][0]   # Komplett falsch
        if text == "VERSE" or text == "CHORUS" or text == "BRIDGE" or text == "OUTRO" or text == "INTRO":
            continue   ## Kann man vielleicht noch erweitern, um auch "PRE-CHORUS" oder "PRE-CHORUS 1" zu erkennen
        print(text)
        if is_chord(text):
            avg_x_pos_of_chord = sum(bbox[_][0] for _ in range(4)) / 4
            _chord = convert_chord_to_nashV(text.replace('?', '').replace('_', ''), key)
            #current_line["chords"][None] = str(_chord)
            
        else:
            avg_width = sum([abs(bbox[1][0] - bbox[0][0]), abs(bbox[3][0] - bbox[2][0])]) / 2
            print(avg_width)
            print([abs(bbox[1][0] - bbox[0][0]), abs(bbox[3][0] - bbox[2][0])])
            start_x = min(bbox[_][0] for _ in range(4))   # könnte auch einfach bbox[0][0] oder bbox[2][0] sein
            if current_line["lyrics"]:
                if avg_x_pos_of_chord:
                    print(current_line["lyrics"])
                    print(len(current_line["lyrics"]))
                    processed_position = process_position(avg_x_pos_of_chord, start_x, avg_width, len(current_line["lyrics"]))
                    current_line["chords"][processed_position] = _chord
                verse_data.append(current_line)
                current_line = {"lyrics": "", "chords": {}}
                avg_x_pos_of_chord = None
            current_line["lyrics"] += text + " "
        print('_____')
    
    if current_line["lyrics"]:
        verse_data.append(current_line)
    
    for line in verse_data:
        line["lyrics"] = line["lyrics"].strip()
    print(verse_data)
    return (name_of_part, verse_data)

