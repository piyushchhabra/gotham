from enum import Enum


class District(Enum):
    BATCAVE = "The Batcave"
    WAYNE_MANOR = "Wayne Manor"
    OLD_GOTHAM = "Old Gotham"
    THE_NARROWS = "The Narrows"
    DIAMOND_DISTRICT = "Diamond District"
    BURNSIDE = "Burnside"
    EAST_END = "East End"
    OTISBURG = "Otisburg"
    ACE_CHEMICALS = "Ace Chemicals"
    GCPD_HQ = "GCPD Headquarters"
    ARKHAM_ISLAND = "Arkham Island"

    @property
    def display_name(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value
