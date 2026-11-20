"""
╔══════════════════════════════════════════════════════════════╗
║         FULLHOUSE HACKATHON — BOT TEMPLATE v1.0             ║
║         No-Limit Texas Hold'em, 6-max                        ║
╚══════════════════════════════════════════════════════════════╝

RULES:
  - Implement the decide() function below. That's it.
  - You may import any stdlib module and any library in requirements.txt
  - You have 2 seconds to return an action or you auto-fold
  - If your function crashes, it auto-folds for that hand

NOT ALLOWED (will DQ your bot):
  - External API calls: no Claude/OpenAI/Anthropic/Google/any HTTP. Network is
    blocked at the container level; trying anyway is a DQ.
  - File writes during gameplay; data/ is read-only and only at import time.
  - subprocess / os.system / shell commands.
  - Threading or async tricks to dodge the 2s/action signal timer.
  - Reflection: __import__('socket'), getattr(__builtins__, 'open'),
    eval(), exec(), compile() — all flagged by the validator.
  - Collusion between bots you've registered with friends — bots must play
    independently; coordinated soft-play or chip-dumping = both DQ'd.
  - Reading other bots' code or hole cards (you can't anyway, but trying = DQ).

OPTIONAL DATA FILES (NEW):
  Submit a .zip archive containing:
    bot.py        (this file, required at root)
    data/         (optional directory with .npz, .pkl, .bin, etc.)

  At module-import time only, you can read from a sibling 'data/' directory:

      import os
      DATA_DIR = os.environ.get("BOT_DATA_DIR",
                                os.path.join(os.path.dirname(__file__), "data"))
      with open(os.path.join(DATA_DIR, "blueprint.npz"), "rb") as f:
          BLUEPRINT = ...load(f)

  Limits:
    - Total submission (bot.py + data/) <= 250 MB
    - data/ alone <= 200 MB
    - bot.py <= 5 MB
    - File access during decide() is blocked at the OS level

CARD FORMAT:
  Cards are strings like "As" (Ace of spades), "Td" (Ten of diamonds)
  Ranks: 2 3 4 5 6 7 8 9 T J Q K A
  Suits: s (spades) h (hearts) d (diamonds) c (clubs)

RETURN FORMAT:
  {"action": "fold"}
  {"action": "check"}          # only valid when amount_owed == 0
  {"action": "call"}
  {"action": "raise", "amount": 1200}   # amount = TOTAL bet, not raise-by
  {"action": "all_in"}

  Invalid actions default to fold. Raises below min_raise_to are snapped up.
"""

"""Bot C: The Shark — tight preflop, position-aware, value bets."""
import random

BOT_NAME = "The Shark"

STRONG_HANDS = {
    ("A", "A"), ("K", "K"), ("Q", "Q"), ("J", "J"), ("T", "T"),
    ("A", "K"), ("A", "Q"), ("A", "J"), ("K", "Q"),
}

def hand_strength(cards):
    ranks = tuple(sorted([c[0] for c in cards], reverse=True))
    suited = cards[0][1] == cards[1][1]
    if ranks in STRONG_HANDS:
        return "strong"
    if ranks[0] in "AKQJT" or suited:
        return "medium"
    return "weak"

def decide(state):
    street  = state["street"]
    owed    = state["amount_owed"]
    pot     = state["pot"]
    stack   = state["your_stack"]
    seat    = state["seat_to_act"]
    n       = len(state["players"])
    potodds = owed/owed
    # Late position = closer to dealer button = more info
    position = seat / max(n - 1, 1)  # 0 = early, 1 = late

    # Preflop: tight hand selection
    if street == "preflop":
        strength = hand_strength(state["your_cards"])

        if strength == "strong":
            raise_to = min(state["min_raise_to"] * 3, stack + state["your_bet_this_street"])
            return {"action": "raise", "amount": raise_to}

        if strength == "medium" and position > 0.5:
            if owed < pot * 0.2:
                return {"action": "call"}

        if state["can_check"]:
            return {"action": "check"}

        return {"action": "fold"}

    # Postflop: position-based value betting
    if state["can_check"]:
        if position > 0.6 and random.random() < 0.4:
            bet = min(int(pot * 0.6), stack + state["your_bet_this_street"])
            bet = max(bet, state["min_raise_to"])
            return {"action": "raise", "amount": bet}
        return {"action": "check"}

    # Calling threshold tightens in early position
    threshold = 0.25 if position > 0.5 else 0.15
    if pot > 0 and owed / pot <= threshold:
        return {"action": "call"}

    return {"action": "fold"}
