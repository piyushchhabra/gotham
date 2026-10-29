"""Sample data for the demo."""

from __future__ import annotations

from decimal import Decimal

from gotham.city import Gotham
from gotham.models.ally import Ally
from gotham.models.district import District as D
from gotham.models.gadget import Gadget, GadgetCategory as C
from gotham.models.villain import Villain

ROADS = [
    (D.BATCAVE, D.WAYNE_MANOR, 2),
    (D.BATCAVE, D.OLD_GOTHAM, 9),
    (D.BATCAVE, D.DIAMOND_DISTRICT, 7),
    (D.WAYNE_MANOR, D.BURNSIDE, 12),
    (D.OLD_GOTHAM, D.THE_NARROWS, 8),
    (D.OLD_GOTHAM, D.GCPD_HQ, 3),
    (D.OLD_GOTHAM, D.EAST_END, 6),
    (D.DIAMOND_DISTRICT, D.GCPD_HQ, 4),
    (D.DIAMOND_DISTRICT, D.OTISBURG, 5),
    (D.EAST_END, D.ACE_CHEMICALS, 7),
    (D.EAST_END, D.THE_NARROWS, 4),
    (D.OTISBURG, D.ACE_CHEMICALS, 6),
    (D.THE_NARROWS, D.ARKHAM_ISLAND, 10),
    (D.BURNSIDE, D.OTISBURG, 5),
]

GADGETS = [
    (Gadget("Batarang", 120, C.THROWABLE, Decimal("85.00")), 40),
    (Gadget("Grapnel Gun", 900, C.GRAPPLE, Decimal("12500.00")), 3),
    (Gadget("Smoke Pellet", 60, C.THROWABLE, Decimal("12.50")), 50),
    (Gadget("Explosive Gel", 300, C.EXPLOSIVE, Decimal("640.00")), 10),
    (Gadget("Cryptographic Sequencer", 450, C.FORENSIC, Decimal("31000.00")), 1),
    (Gadget("Rebreather", 200, C.MEDICAL, Decimal("980.00")), 4),
    (Gadget("Antidote Kit", 250, C.MEDICAL, Decimal("1450.00")), 6),
    (Gadget("Comm Link", 80, C.COMMUNICATION, Decimal("2200.00")), 8),
]


def seed(gotham: Gotham) -> Gotham:
    for a, b, minutes in ROADS:
        gotham.city_map.add_road(a, b, minutes)

    for gadget, quantity in GADGETS:
        gotham.inventory.register(gadget, quantity)

    for ally in [
        Ally("A1", "Batman", D.BATCAVE, {"detective", "combat", "stealth", "hacking"}),
        Ally("A2", "Nightwing", D.BURNSIDE, {"acrobatics", "combat"}),
        Ally("A3", "Batgirl", D.GCPD_HQ, {"hacking", "combat"}),
        Ally("A4", "Red Hood", D.EAST_END, {"combat", "firearms"}),
        Ally("A5", "Oracle", D.OLD_GOTHAM, {"hacking"}),
    ]:
        gotham.allies.save(ally)

    for villain in [
        Villain("V1", "The Joker", None, 10),
        Villain("V2", "The Penguin", "Oswald Cobblepot", 6),
        Villain("V3", "The Riddler", "Edward Nygma", 7),
        Villain("V4", "Two-Face", "Harvey Dent", 7),
        Villain("V5", "Poison Ivy", "Pamela Isley", 6),
        Villain("V6", "Scarecrow", "Jonathan Crane", 8),
        Villain("V7", "Mr. Freeze", "Victor Fries", 7),
        Villain("V8", "Catwoman", "Selina Kyle", 4),
    ]:
        gotham.villains.save(villain)

    return gotham
