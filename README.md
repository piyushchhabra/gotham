# Gotham City Operations Platform

The software that keeps Gotham running after dark. It covers the Batcave armoury, the Bat-Signal
dispatch system, the Batmobile route planner, GCPD case management, Arkham Asylum intake, threat
assessment for the rogues gallery, Wayne Enterprises' off-the-books budgets, and crime statistics
for Commissioner Gordon. It's written in pure Python 3.10+ and uses no runtime dependencies.

> **Bug bash practice repo.** This codebase has bugs planted in it on purpose, and some tests fail
> because of them. Each bug is filed as a [GitHub issue](../../issues) that describes what users
> see, not what causes it. Your job is to reproduce the bug, find the root cause, fix it, and make
> the test suite pass without changing what the tests expect.

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest                          # run the test suite (some tests fail on purpose)
pytest tests/test_dispatch.py   # run one module
python -m gotham                # run the demo night in Gotham
```

## Project layout

```
gotham/
├── __main__.py         # demo entry point
├── city.py             # Gotham: wires every repository and service together
├── seed.py             # sample road network, gadgets, allies and villains
├── exceptions.py       # domain errors
├── repository.py       # generic in-memory repository
├── models/             # Villain, Ally, Gadget, Case, Inmate/Wing, District
└── services/
    ├── batcave.py      # gadget inventory and utility belts
    ├── patrol.py       # road network and Batmobile route planning
    ├── dispatch.py     # the Bat-Signal
    ├── gcpd.py         # GCPD cases and villain dossiers
    ├── arkham.py       # Arkham Asylum
    ├── threat.py       # threat scores and the most-wanted list
    ├── finance.py      # Wayne Enterprises budgets
    └── crime_stats.py  # crime statistics
tests/                  # pytest suite
```

## Domain rules

| Area | Module | Rules |
|------|--------|-------|
| Utility belt | `services/batcave.py` | A belt has 8 pouches and a 2,000 g weight limit. A belt loaded to exactly the limit is fine. Equipping a gadget takes it out of Batcave stock, and unequipping puts it back. `auto_loadout` works through a wishlist in order and skips anything that won't fit or is out of stock. |
| Route planning | `services/patrol.py` | Roads have a travel time in minutes and can be one-way or closed. `shortest_route` returns the fastest route, which isn't necessarily the one with the fewest stops. A patrol visits each checkpoint in order and returns to the start. |
| Bat-Signal | `services/dispatch.py` | The signal goes to the available ally with the shortest travel time, with ties broken alphabetically by codename. A skill can be required. A citywide alert sends the N fastest allies. Once an ally stands down, they're available again at the incident's location. |
| GCPD | `services/gcpd.py` | Case IDs are `GCPD-0001`, `GCPD-0002` and so on. Unassigned cases that have been open for 90 days or more go cold. Active cases are sorted by severity, then age. Solving a case with a culprit puts the culprit in custody. A dossier summarises one villain's record. |
| Arkham | `services/arkham.py` | Wing A takes threat level 8+ (3 cells), wing B takes 5-7 (5 cells), and wing C takes the rest (10 cells). Cells are given out lowest-number first. Only villains in GCPD custody can be admitted. Inmates are released on or after their release date. An escape puts the villain back at large. |
| Threat | `services/threat.py` | Score = 10 × threat level, plus 5 per known associate, plus 15 if at large, plus 8 per escape, plus 3 per open case. Bands: low (under 50), elevated (50+), high (80+), critical (110+). |
| Finance | `services/finance.py` | All amounts are `Decimal` and rounded to the cent, with halves rounded up. Orders of 10 or more get a 10% bulk discount. A division can't spend more than its remaining budget. |
| Crime stats | `services/crime_stats.py` | The hotspot is the district with the highest total severity of active cases, with ties broken alphabetically. Also reports the clearance rate and the average number of days to solve a case. |

## How to run a bug bash

1. Pick an open issue.
2. Reproduce it, either with the failing test or by writing a new one.
3. Find the root cause. Sometimes the code that breaks isn't the code that's wrong, and tests that pass can mislead you.
4. Fix it with the smallest change you can, and explain why the fix works.
5. Run `pytest` and check that nothing else broke.
