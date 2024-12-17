import json
import re
from typing import List, Dict, Tuple

def is_chord(text: str) -> bool:
    """Check if the text is likely a chord."""
    basic_chords = {"C", "D", "E", "F", "G", "A", "B", "H"}
    text = text.upper()
    if len(text) > 1: 
        return len(text) <= 4 and any(char in text for char in ["7", "6", "9", "m", "M", "maj", "dim", "aug", "sus", "add", "°", "ø", "b", "#", "/"])
    return text in basic_chords

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
    if relativ_x > 0:   
        pos  = int((relativ_x/avg_width) * length_of_lyrics)
        return pos
    else:
        print('DEBUG ERROR: relativ_x is negative')
        return None

from typing import List, Tuple

def cluster_to_lines(ocr_result: List[Tuple], y_threshold: int = 10) -> List[List[int]]:
    """
    Groups OCR result bounding boxes into lines based on their y-coordinates.

    Args:
        ocr_result (List[Tuple]): OCR results containing bounding boxes and text.
        y_threshold (int): Maximum vertical distance to consider for the same line.

    Returns:
        List[List[int]]: A list of lists where each sublist contains the indices of the OCR results in the same line.
    """
    lines = []
    current_line = []
    current_y = None

    # Sort OCR results by the top-left `y` coordinate to ensure proper processing
    sorted_results = sorted(enumerate(ocr_result[0]), key=lambda item: item[1][0][0][1])  # Sort by bbox top-left y

    for i, line in sorted_results:
        bbox, (text, confidence) = line
        avg_y = sum([point[1] for point in bbox]) / 4  # Average y-coordinate of the bounding box

        if current_y is None or abs(avg_y - current_y) < y_threshold:  # Same line
            current_line.append(i)
            current_y = avg_y
        else:  # New line
            lines.append(current_line)
            current_line = [i]
            current_y = avg_y

    # Add the last line
    if current_line:
        lines.append(current_line)

    return lines


def process_ocr_result(ocr_result: list, key:str, name_of_part:str) -> tuple[str,str]:
    verse_data = []
    #current_line = {"lyrics": "", "chords": {}}
    _chord = None
    avg_x_pos_of_chord = None
    

    line_numbers = cluster_to_lines(ocr_result)

    ### Maybe add a VERSE/CHORUS/BRIDGE/OUTRO/INTRO detection here

    # For each line, check if it is a chord line or a lyric line
    for i, line_nrs in enumerate(line_numbers): 
        line_data = {}  
        if all ([is_chord(ocr_result[0][nr][1][0]) for nr in line_nrs]):      # Is chordline
            #print(f"Line {i} is a chord: {line_nrs} with data {[ocr_result[0][_][1][0] for _ in line_nrs ]}")
            for nr in line_nrs:
                bbox, (text, confidence) = ocr_result[0][nr]
                avg_x_pos_of_chord = sum(bbox[_][0] for _ in range(4)) / 4
                _chord = convert_chord_to_nashV(text.replace('?', '').replace('_', ''), key)
                line_data[nr] = {'avg_x': avg_x_pos_of_chord, 'chord':_chord}
            line_numbers[i] = {'type': 'chords' ,'data':line_data}
            
        else:
            #print(f"Line {i} is a lyric: {line_nrs} with data {[ocr_result[0][_][1][0] for _ in line_nrs ]}")
            for nr in line_nrs:
                bbox, (text, confidence) = ocr_result[0][nr]                                       # Is lyricline
                avg_width = sum([abs(bbox[1][0] - bbox[0][0]), abs(bbox[3][0] - bbox[2][0])]) / 2
                start_x = min(bbox[_][0] for _ in range(4))   # könnte auch einfach bbox[0][0] oder bbox[2][0] sein
                line_data[nr] = {'start_x': start_x, 'avg_width': avg_width, 'text': text, }
                
            line_numbers[i] = {'type': 'lyrics' ,'data':line_data}
    
    
    ### Group into Lyrics and Chords pairs

    ### get Position of Chords relative to Lyrics

    return (name_of_part, verse_data)





    #for i, item in enumerate(ocr_result):
    #    bbox, text, _prob = item    # I think _ is prob, but not sure
    #    print(text)
    #    x = bbox[0][0]   # Komplett falsch
    #    if text == "VERSE" or text == "CHORUS" or text == "BRIDGE" or text == "OUTRO" or text == "INTRO":
    #        continue   ## Kann man vielleicht noch erweitern, um auch "PRE-CHORUS" oder "PRE-CHORUS 1" zu erkennen
    #    
    #    if is_chord(text):
    #        avg_x_pos_of_chord = sum(bbox[_][0] for _ in range(4)) / 4
    #        _chord = convert_chord_to_nashV(text.replace('?', '').replace('_', ''), key)
#
    #        
    #    else:
    #        avg_width = sum([abs(bbox[1][0] - bbox[0][0]), abs(bbox[3][0] - bbox[2][0])]) / 2
    #        start_x = min(bbox[_][0] for _ in range(4))   # könnte auch einfach bbox[0][0] oder bbox[2][0] sein
    #        if current_line["lyrics"]:
    #            if avg_x_pos_of_chord:
    #                processed_position = process_position(avg_x_pos_of_chord, start_x, avg_width, len(current_line["lyrics"]))
    #                current_line["chords"][processed_position] = _chord
    #            verse_data.append(current_line)
    #            current_line = {"lyrics": "", "chords": {}}
    #            avg_x_pos_of_chord = None
    #        current_line["lyrics"] += text + " "
    #    
    #
    #if current_line["lyrics"]:
    #    verse_data.append(current_line)
    #
    #for line in verse_data:
    #    line["lyrics"] = line["lyrics"].strip()
    #
    #return (name_of_part, verse_data)

