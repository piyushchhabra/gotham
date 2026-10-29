"""A night in Gotham. Run with ``python -m gotham``."""

from __future__ import annotations

from datetime import date

from gotham.city import Gotham
from gotham.models.case import Severity
from gotham.models.district import District
from gotham.seed import seed


def main() -> None:
    gotham = seed(Gotham())
    today = date(2026, 10, 29)

    print("== GCPD ==")
    heist = gotham.gcpd.open_case("Diamond exchange heist", District.DIAMOND_DISTRICT, Severity.MAJOR, today)
    gas = gotham.gcpd.open_case("Fear toxin in the water supply", District.THE_NARROWS, Severity.CITYWIDE, today)
    gotham.gcpd.add_suspect(heist.case_id, "V8")
    gotham.gcpd.add_suspect(gas.case_id, "V6")
    gotham.gcpd.assign(gas.case_id, "Det. Renee Montoya")
    for case in gotham.gcpd.active_cases():
        print(f"{case.case_id} [{case.severity.name}] {case.title} ({case.district})")

    print("\n== Bat-Signal ==")
    dispatch = gotham.bat_signal.raise_signal(District.THE_NARROWS, Severity.CITYWIDE)
    print(f"{dispatch.codename} -> {dispatch.district}, ETA {dispatch.eta_minutes} min")
    print("Route: " + " -> ".join(str(stop) for stop in dispatch.route.stops))

    print("\n== Utility belt ==")
    belt = gotham.new_utility_belt()
    loaded = belt.auto_loadout(["Grapnel Gun", "Batarang", "Batarang", "Smoke Pellet", "Antidote Kit", "Rebreather"])
    print(", ".join(loaded), f"({belt.total_weight} g)")

    print("\n== Arkham ==")
    gotham.gcpd.solve(gas.case_id, today, culprit_id="V6")
    inmate = gotham.arkham.admit("V6", today, sentence_days=365)
    print(f"Scarecrow admitted to cell {inmate.cell}, eligible for release {inmate.release_date}")

    print("\n== Most wanted ==")
    for villain in gotham.threats.most_wanted(gotham.villains.all()):
        print(f"{villain.alias}: {gotham.threats.score(villain)} ({gotham.threats.classify(villain).value})")

    print("\n== Wayne Enterprises ==")
    gotham.finance.purchase_gadgets(gotham.inventory, "Batarang", 50, today)
    print(f"Applied Sciences remaining: ${gotham.finance.remaining('Applied Sciences'):,}")


if __name__ == "__main__":
    main()
