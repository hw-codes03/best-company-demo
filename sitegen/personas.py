"""The three people who can appear in images, with their names written for each locale.

- Jordan Vale is the OUTDATED persona. Every image showing Jordan Vale must be replaced.
- Priya Nair is the APPROVED persona. Images showing Priya are already correct.
- Jordan Vail is a DECOY: a different person with a near-identical name and the same
  initials. Images of Jordan Vail must NOT be replaced.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    key: str                # short id used in the answer key
    status: str             # "outdated", "approved" or "decoy"
    email: str              # always an example.com address
    initials: str           # drawn inside the avatar circle
    avatar_color: str       # avatar background colour (hex)
    avatar_color_name: str  # the same colour in words, for the answer key
    # Name forms per locale. An image picks one form from its locale's list, so
    # Japanese and Arabic images sometimes add the Latin name in brackets.
    names: dict


JORDAN_VALE = Persona(
    key="jordan_vale",
    status="outdated",
    email="jordan.vale@example.com",
    initials="JV",
    avatar_color="#0F9D9A",
    avatar_color_name="teal",
    names={
        "en-US": ["Jordan Vale"],
        "ja-JP": ["ジョーダン・ヴェール", "ジョーダン・ヴェール（Jordan Vale）"],
        "ar-SA": ["جوردان فيل", "جوردان فيل (Jordan Vale)"],
    },
)

PRIYA_NAIR = Persona(
    key="priya_nair",
    status="approved",
    email="priya.nair@example.com",
    initials="PN",
    avatar_color="#F28C28",
    avatar_color_name="orange",
    names={
        "en-US": ["Priya Nair"],
        "ja-JP": ["プリヤ・ナイル", "プリヤ・ナイル（Priya Nair）"],
        "ar-SA": ["بريا ناير", "بريا ناير (Priya Nair)"],
    },
)

# The decoy shares the initials "JV" and differs from Jordan Vale by one or two
# letters in every script, but has a different email and a purple avatar.
JORDAN_VAIL = Persona(
    key="jordan_vail",
    status="decoy",
    email="jordan.vail@example.com",
    initials="JV",
    avatar_color="#6B5BA8",
    avatar_color_name="purple",
    names={
        "en-US": ["Jordan Vail"],
        "ja-JP": ["ジョーダン・ベイル", "ジョーダン・ベイル（Jordan Vail）"],
        "ar-SA": ["جوردان فايل", "جوردان فايل (Jordan Vail)"],
    },
)

ALL_PERSONAS = {p.key: p for p in (JORDAN_VALE, PRIYA_NAIR, JORDAN_VAIL)}
