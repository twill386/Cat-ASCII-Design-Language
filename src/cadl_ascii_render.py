"""
ASCII renderer for CADL cats
"""

from typing import Dict, Any

# Ears
####################################################################
def ears_fragment(ears: str) -> str:
    ears = (ears or "pointy").lower()

    if ears == "pointy":
        return " /\\   /\\ "
    if ears == "droopy":
        return " /\\_ /\\_ "
    if ears == "round":
        return " (o   o) "
    if ears == "long":
        return "/\\     /\\"
    if ears == "short":
        return " /\\_/\\  "

    # fallback
    return " /\\   /\\ "

# Mood & Mouth (Cat's Expression)
####################################################################
def eyes_for_mood(mood: str) -> str:
    mood = (mood or "").lower()

    if mood == "sleepy":
        return "-.-"
    if mood == "happy":
        return "^.^"
    if mood == "excited":
        return "O.O"
    if mood == "loving":
        return "*.*"
    if mood == "curious":
        return "o.o"
    if mood == "angry":
        return "¬.¬"
    return "o.o"   # default expression


def mouth_char(mouth: str) -> str:
    mouth = (mouth or "neutral").lower()

    if mouth == "smile":
        return "_"
    if mouth == "frown":
        return "~"
    if mouth == "open":
        return "o"
    if mouth == "smirk":
        return "/"
    return "-"  # neutral


def core_face(mood: str, mouth: str) -> str:
    eyes = eyes_for_mood(mood)
    m = mouth_char(mouth)
    # replace middle eye char with mouth char
    return eyes[0] + m + eyes[2]

# Whiskers
####################################################################
def whiskers(whiskers: str):
    whiskers = (whiskers or "long").lower()

    if whiskers == "long":
        return "=", "="
    if whiskers == "short":
        return "-", "-"
    if whiskers == "curled":
        return "~", "~"

    return "-", "-"  # fallback

# Body, Face boundary shape
####################################################################
# normal = ( face )
# smooth = | face |
# fluffy = { face }
# chubby = (  face  ) (one extra space)
####################################################################
def wrap_face(body: str, face: str) -> str:
    body = (body or "normal").lower()

    if body == "smooth":
        return f"| {face} |"
    if body == "fluffy":
        return f"{{ {face} }}"
    if body == "chubby":
        # one extra space for chunky boy
        return f"(  {face}  )"

    # normal
    return f"( {face} )"


# Tail (bottom line, right aligned, none will hide it)
####################################################################
def tail_fragment(tail: str):
    if tail is None:
        return None

    tail = tail.lower()

    if tail == "none":
        return None
    if tail == "fluffy":
        return "~~>"
    if tail == "curled":
        return "~~"
    if tail == "straight":
        return "-->"

    # default
    return "-->"

# Main Function for the renderer
####################################################################
def render_cat(cat: Dict[str, Any]) -> str:
    """
    Render a CADL cat object (as produced by your interpreter) to ASCII.

    Expects:
        cat = {
            "type": "cat",
            "traits": {
                "ears": ...,
                "mouth": ...,
                "body": ...,
                "tail": ...,
                "whiskers": ...,
                "mood": ...
            }
        }
    """
    if not isinstance(cat, dict) or cat.get("type") != "cat":
        raise TypeError("render_cat expected a cat object with type='cat'")

    traits = cat.get("traits", {})

    ears = traits.get("ears")
    mouth = traits.get("mouth")
    body = traits.get("body")
    tail = traits.get("tail")
    whiskers = traits.get("whiskers")
    mood = traits.get("mood")

    #### Build head pieces ####

    ears_raw = ears_fragment(ears)

    core = core_face(mood, mouth)
    wrapped_face = wrap_face(body, core)

    left_w, right_w = whiskers(whiskers)
    prefix = f"{left_w} "
    suffix = f" {right_w}"

    face_line_raw = prefix + wrapped_face + suffix  # full head line with whiskers
    head_width = len(face_line_raw)

    #### Place ears centered over face structure (wrapped) ####

    face_start = len(prefix)
    face_len = len(wrapped_face)
    ears_len = len(ears_raw)

    # center ears over the face structure within the head width
    ear_start = (2 * face_start + face_len - ears_len) // 2
    if ear_start < 0:
        ear_start = 0

    ears_line_head = " " * ear_start + ears_raw
    if len(ears_line_head) < head_width:
        ears_line_head = ears_line_head.ljust(head_width)

    #### Tail line ####

    tail_frag = tail_fragment(tail)  
    if tail_frag is None:
        tail_line_raw = None
        total_width = head_width
    else:
        tail_line_raw = tail_frag
        total_width = max(head_width, len(tail_line_raw))

    #### Final padding to total width ####

    # Center head (ears + face)
    head_pad = (total_width - head_width) // 2
    final_ears = (" " * head_pad) + ears_line_head
    final_ears = final_ears.ljust(total_width)

    final_face = (" " * head_pad) + face_line_raw
    final_face = final_face.ljust(total_width)

    lines = [final_ears, final_face]

    # Tail right-aligned if present
    if tail_line_raw is not None:
        tail_line = tail_line_raw.rjust(total_width)
        lines.append(tail_line)

    return "\n".join(lines)