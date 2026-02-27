import ollama
from pathlib import Path

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  setup_knowledge.py
#  Run this ONCE before using mod.py or scanner.py
#  Uses Llama3 to research Roblox and build a knowledge
#  file that Moondream reads before every avatar check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEXT_MODEL    = "llama3"
KNOWLEDGE_FILE = Path("knowledge.txt")

QUESTIONS = [
    (
        "what_is_roblox",
        "Describe what Roblox is in 3-4 sentences. Focus on: who plays it, the age range of players, and that avatars are blocky 3D characters."
    ),
    (
        "base_avatar",
        "Describe what a default Roblox avatar looks like visually. Include: the blocky shape, body color options including unnatural colors like neon green or blue, R6 vs R15 body types, and the fact that many avatars wear no shirt or pants and just show their body color which is completely normal."
    ),
    (
        "avatar_variety",
        "Describe the huge variety of Roblox avatar styles in detail. Include: anime style avatars, dark/goth aesthetics, animal and creature avatars, avatars with horns/tails/wings, military outfits, fully armored avatars, avatars with long anime hair, avatars that look naked but are just using body color with no clothes which is fine, and feminine style avatars on any gender which are also fine."
    ),
    (
        "normal_outfits",
        "List and describe normal acceptable Roblox outfits that should NEVER be flagged as inappropriate. Include: hoodies, t-shirts with graphics, jeans, shorts, skirts, crop tops, thigh highs worn with a full outfit, armor sets, animal costumes, dark all-black outfits, Minecraft themed outfits, anime outfits, military uniforms, and avatars with no clothes but solid non-skin body color."
    ),
    (
        "inappropriate_outfits",
        "Describe what makes a Roblox avatar outfit inappropriate for a 13+ social hangout game. Be specific and visual. Include: skin-colored full body texture that looks naked, shiny latex or rubber suits, lingerie as a main outfit, revealing harness tops that expose most of the chest, cutout tops that expose chest sexually, skin-colored bodysuits with thigh high socks which is a very common inappropriate combo, and any outfit where the clear intent is to look naked or sexual."
    ),
    (
        "edge_cases",
        "Describe the hardest edge cases when moderating Roblox avatars. Include: the difference between a short crop top that's fine vs a revealing harness that should be flagged, the difference between short shorts that are fine vs a skin-colored bodysuit that should be flagged, avatars with exposed midriff that might be borderline, dark outfits with small cutouts that might be fine, and feminine outfits that are completely acceptable vs feminine outfits that cross into inappropriate territory."
    ),
    (
        "moderation_rules",
        "Write a concise set of moderation rules for a Roblox avatar AI checker. The game is a social hangout rated 13+. Rules should cover: what to flag, what never to flag, how to handle edge cases, and how to treat feminine or unusual avatars fairly without over-flagging. Be specific and practical."
    ),
]

def ask(prompt: str) -> str:
    print(f"  Researching...", end=" ", flush=True)
    try:
        response = ollama.chat(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert on Roblox games and content moderation. "
                        "Give detailed, accurate, practical answers. "
                        "Focus on visual descriptions that would help an AI vision model "
                        "identify inappropriate avatars in screenshots."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        result = response["message"]["content"].strip()
        print("done")
        return result
    except Exception as e:
        print(f"error: {e}")
        return ""

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  roblox-auto-mod — Knowledge Setup")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("\nThis will use Llama3 to research Roblox and build")
print("a knowledge file for the AI to use during moderation.")
print("\nMake sure you have run: ollama pull llama3")
print("And that ollama serve is running.\n")

# Check Llama3 is available
print("Checking Llama3...")
try:
    ollama.chat(model=TEXT_MODEL, messages=[{"role": "user", "content": "hi"}])
    print("Llama3 ready.\n")
except Exception as e:
    print(f"\nError: could not connect to Llama3 — {e}")
    print("Make sure ollama is running (ollama serve) and you have pulled the model:")
    print("  ollama pull llama3")
    exit(1)

# Research each topic
print(f"Researching {len(QUESTIONS)} topics about Roblox moderation...\n")
sections = {}
for key, question in QUESTIONS:
    print(f"[{key}]")
    answer = ask(question)
    sections[key] = answer
    print()

# Build the knowledge file
print("Building knowledge.txt...")
lines = [
    "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "# roblox-auto-mod — AI Knowledge Base",
    "# Generated automatically by setup_knowledge.py",
    "# You can edit this file to add your own game-specific rules",
    "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "",
]

labels = {
    "what_is_roblox":      "WHAT IS ROBLOX",
    "base_avatar":         "WHAT A BASE AVATAR LOOKS LIKE",
    "avatar_variety":      "HOW AVATARS CAN DIFFER",
    "normal_outfits":      "NORMAL OUTFITS — DO NOT FLAG",
    "inappropriate_outfits": "INAPPROPRIATE OUTFITS — FLAG THESE",
    "edge_cases":          "EDGE CASES",
    "moderation_rules":    "MODERATION RULES",
}

for key, label in labels.items():
    if sections.get(key):
        lines.append(f"[{label}]")
        lines.append(sections[key])
        lines.append("")

KNOWLEDGE_FILE.write_text("\n".join(lines))
print(f"Saved to {KNOWLEDGE_FILE}\n")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Knowledge setup complete!")
print("You can open knowledge.txt and edit it to add your own rules.")
print("Next step: run prep.py to label some avatars, then you're ready to go.")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
