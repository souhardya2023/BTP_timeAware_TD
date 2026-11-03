"""COCOMO II effort for a size in SLOC.   PM = A * KSLOC^E * prod(EM),   E = B + 0.01 * sum(SF)

Two presets:
  nominal  A=2.94, B=0.91, all five scale factors nominal (sum 18.97 -> E = 1.0997), EM = 1   (COCOMO II.2000 post-architecture)
  paper    A=2.64, E=0.91, EM = 1   (the constants used in the notes/paper summary; E=0.91 means every scale factor at its best rating)
The constants of the 2025 paper could not be checked from the notes, so both are available and `PRESET` is the one place to change.
"""
PRESETS = {
    "nominal": dict(A=2.94, E=0.91 + 0.01 * 18.97, EM=1.0),
    "paper": dict(A=2.64, E=0.91, EM=1.0),
}
PRESET = "nominal"


def pm(sloc, preset=None):
    p = PRESETS[preset or PRESET]
    if sloc <= 0:
        return 0.0
    return p["A"] * (sloc / 1000.0) ** p["E"] * p["EM"]
