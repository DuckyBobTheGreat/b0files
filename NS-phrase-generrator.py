"""
generate_nsfw_phrases.py
------------------------
Generates a comprehensive NSFW phrase library with thousands of common
variants: body parts, sexual acts, fluid terms, fetishes, gender references,
and euphemisms.

Outputs:
    nsfw_phrases_generated.json

You can load this in your main NSFW scanner:
    with open("nsfw_phrases_generated.json") as f:
        NSFW_PHRASES.update(json.load(f))
"""

import json

# ======================================================
# 🔧 CONFIGURATION
# ======================================================

OUTPUT_FILE = "nsfw_phrases_generated.json"

# Base tokens used to generate combinations
BODYPARTS_ON = [
    "face", "tits", "chest", "body", "belly", "back", "ass", "feet",
    "legs", "hair", "stomach", "breasts"
]

BODYPARTS_IN = ["mouth", "pussy", "vagina", "ass", "anus"]

SEX_ACTS = [
    "sex", "blowjob", "handjob", "footjob", "boobjob", "titjob", "anal",
    "creampie", "threesome", "foursome", "orgy", "masturbation"
]

ADJ_EROTIC = [
    "sexy", "naughty", "hot", "cheeky", "flirty", "provocative", "tempting",
    "seductive", "suggestive", "spicy", "sultry", "sensual", "erotic",
    "passionate", "pleasurable", "kinky", "dirty", "filthy", "wild", "steamy"
]

GENDERS = [
    "girl", "boy", "woman", "man", "lady", "guy", "milf", "dilf",
    "femboy", "trap", "crossdresser", "ladyboy", "transgirl", "transwoman"
]

ROLES = [
    "teacher", "student", "maid", "nurse", "secretary", "bunny", "cop",
    "nun", "wife", "husband", "neighbor", "boss", "employee", "waitress"
]

LOCATIONS = [
    "shower", "bath", "beach", "car", "hotel", "office", "kitchen",
    "couch", "sofa", "bathroom", "pool", "bedroom"
]

FETISHES = [
    "bondage", "bdsm", "foot fetish", "feet pics", "water sports",
    "golden shower", "pee play", "spit roast", "nipple play", "oil play",
    "lotion play", "wax play", "ice play", "tentacle sex", "milking",
    "squirting", "female ejaculation", "bukkake", "humiliation",
    "submission", "dominatrix", "rope play", "handcuffed", "leash play"
]

PHRASE_BASE = [
    "cum on {bodypart}", "cum over {bodypart}", "cum all over {bodypart}",
    "cum in {bodypart}", "cum inside {bodypart}", "cover {bodypart} in cum",
    "covered in cum", "dripping with cum", "dripping wet", "post orgasm",
    "after orgasm", "wet orgasm", "creampie leak", "creampie oozing",
    "see through {garment}", "no {garment}", "pov {act}",
    "{location} sex", "in the {location}", "{location} creampie",
    "{erotic} {gender}", "{erotic} {role}", "{erotic} {location}",
    "{erotic} couple", "naughty {gender}", "cheeky {gender}",
    "dominant {gender}", "submissive {gender}", "sexy {role}",
    "hot {role}", "naughty {role}"
]

GARMENTS = ["bra", "panties", "lingerie", "dress", "bikini", "outfit"]

# ======================================================
# 🧩 GENERATION LOGIC
# ======================================================

def generate_phrases():
    phrases = set()

    # Core explicit combos
    for part in BODYPARTS_ON:
        for template in [
            f"cum on {part}", f"cum over {part}", f"cum all over {part}",
            f"cover {part} in cum", f"covered in cum"
        ]:
            phrases.add(template)

    for part in BODYPARTS_IN:
        for template in [
            f"cum in {part}", f"cum inside {part}", f"filled with cum",
            f"{part} creampie", f"{part} creampie leak", f"{part} creampie oozing"
        ]:
            phrases.add(template)

    # Act-based
    for act in SEX_ACTS:
        phrases.update({
            f"pov {act}", f"first person {act}",
            f"public {act}", f"amateur {act}", f"homemade {act}"
        })

    # Garment-based
    for g in GARMENTS:
        phrases.update({
            f"see through {g}", f"see thru {g}",
            f"no {g}", f"{g} off", f"transparent {g}"
        })

    # Location-based
    for loc in LOCATIONS:
        phrases.update({
            f"{loc} sex", f"sex in {loc}", f"{loc} creampie",
            f"public {loc} sex", f"caught in {loc}", f"naughty {loc} scene"
        })

    # Fetishes
    for f in FETISHES:
        phrases.add(f)
        if " " in f:
            phrases.add(f.replace(" ", "_"))
            phrases.add(f.replace(" ", "-"))

    # Gender/erotic adjectives/roles
    for adj in ADJ_EROTIC:
        for g in GENDERS:
            phrases.add(f"{adj} {g}")
            phrases.add(f"{adj} {g}s")
        for r in ROLES:
            phrases.add(f"{adj} {r}")
        for loc in LOCATIONS:
            phrases.add(f"{adj} {loc}")

    # Mix with templates
    for base in PHRASE_BASE:
        for part in BODYPARTS_ON + BODYPARTS_IN + GARMENTS + LOCATIONS + GENDERS + ROLES:
            phrase = base.format(
                bodypart=part, garment=part, location=part,
                erotic="{erotic}", gender="{gender}", role="{role}", act="{act}"
            )
            if not any(x in phrase for x in ["{erotic}", "{gender}", "{role}", "{act}"]):
                phrases.add(phrase)

    # Final cleanup and normalization
    phrases = {p.lower().strip() for p in phrases if len(p) > 3}
    print(f"✅ Generated {len(phrases):,} NSFW phrase variants.")
    return sorted(phrases)


def save_phrases(phrases):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(phrases, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {OUTPUT_FILE}")


# ======================================================
# 🏁 MAIN
# ======================================================

if __name__ == "__main__":
    all_phrases = generate_phrases()
    save_phrases(all_phrases)
