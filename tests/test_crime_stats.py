from datetime import timedelta

from gotham.models.case import Severity
from gotham.models.district import District

from tests.conftest import TODAY


def open_case(gotham, district, severity, days_ago=0):
    return gotham.gcpd.open_case("case", district, severity, TODAY - timedelta(days=days_ago))


def test_empty_city_has_no_stats(gotham):
    assert gotham.stats.hotspot() is None
    assert gotham.stats.clearance_rate() == 0.0
    assert gotham.stats.average_days_to_solve() is None


def test_cases_by_district(gotham):
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.EAST_END, Severity.MAJOR)
    solved = open_case(gotham, District.BURNSIDE, Severity.MINOR)
    gotham.gcpd.solve(solved.case_id, TODAY)

    assert gotham.stats.cases_by_district() == {District.EAST_END: 2, District.BURNSIDE: 1}
    assert gotham.stats.cases_by_district(active_only=True) == {District.EAST_END: 2}


def test_severity_histogram(gotham):
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.OTISBURG, Severity.CITYWIDE)
    histogram = gotham.stats.severity_histogram()
    assert histogram[Severity.MINOR] == 2
    assert histogram[Severity.CITYWIDE] == 1
    assert histogram[Severity.MAJOR] == 0


def test_hotspot_weights_by_severity(gotham):
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.ACE_CHEMICALS, Severity.MAJOR)
    assert gotham.stats.hotspot() is District.ACE_CHEMICALS


def test_hotspot_tie_goes_alphabetically(gotham):
    open_case(gotham, District.OTISBURG, Severity.SERIOUS)
    open_case(gotham, District.BURNSIDE, Severity.SERIOUS)
    assert gotham.stats.hotspot() is District.BURNSIDE


def test_clearance_rate_and_average_time_to_solve(gotham):
    a = open_case(gotham, District.EAST_END, Severity.MINOR, days_ago=10)
    b = open_case(gotham, District.EAST_END, Severity.MINOR, days_ago=4)
    open_case(gotham, District.EAST_END, Severity.MINOR)
    open_case(gotham, District.EAST_END, Severity.MINOR)
    gotham.gcpd.solve(a.case_id, TODAY)
    gotham.gcpd.solve(b.case_id, TODAY)

    assert gotham.stats.clearance_rate() == 0.5
    assert gotham.stats.average_days_to_solve() == 7.0
