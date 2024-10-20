import json
import re
from typing import List, Dict, Tuple

def is_chord(text: str) -> bool:
    """Check if the text is likely a chord."""
    return len(text) <= 4 and any(char.isalpha() for char in text)


def convert_chord_to_nashV(chord: str, key: str) -> int:
    """
    Convert a chord to its Nashville number system equivalent based on the key.
    This handles extended chords like F#m7, Cmaj7, B7 by focusing on the base chord.
    """
    # Load Nashville system from a JSON file or define it as a dict here
    nashville_system = json.load(open("nashville_system.json"))

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
        if nash_chord == base_chord_name or (base_chord_name.endswith("m") and nash_chord.startswith(base_chord_name[:-1])):
            return int(nash_num)
    
    # If the chord is not found, return an error or a default value
    return None
    #raise ValueError(f"Chord {chord} not recognized in the key of {key}.")

def process_ocr_result(ocr_result: List[Tuple], key:str, name_of_part:str) -> tuple[str,str]:
    verse_data = []
    current_line = {"lyrics": "", "chords": {}}
    
    for item in ocr_result:
        bbox, text, _ = item
        x = bbox[0][0]
        
        if text == "VERSE" or text == "CHORUS" or text == "BRIDGE" or text == "OUTRO" or text == "INTRO":
            continue   ## Kann man vielleicht noch erweitern, um auch "PRE-CHORUS" oder "PRE-CHORUS 1" zu erkennen
        
        if is_chord(text):
            chord_int = convert_chord_to_nashV(text.replace('?', '').replace('_', ''), key)
            current_line["chords"][str(x)] = str(chord_int)
        else:
            if current_line["lyrics"]:
                verse_data.append(current_line)
                current_line = {"lyrics": "", "chords": {}}
            current_line["lyrics"] += text + " "
    
    if current_line["lyrics"]:
        verse_data.append(current_line)
    
    for line in verse_data:
        line["lyrics"] = line["lyrics"].strip()
    
    return (name_of_part, verse_data)

