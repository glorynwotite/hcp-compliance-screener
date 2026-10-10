"""Tests that each rule catches what it should and ignores clean records."""
from screener.rules import (check_entertainment, check_fair_market_value, check_gifts,
                            check_meal_frequency, check_meal_limit, check_sunshine_fields)


def rec(**kw):
    base = dict(record_id="T1", hcp_npi="1003000001", hcp_name="Dr. Test", specialty="Primary Care",
                date="2026-08-01", nature_of_payment="Meal", amount="80", attendees="4", hours="",
                venue="Clinic office", rep_name="Rep", notes="Lunch with presentation.")
    base.update(kw)
    return base


def test_clean_meal_passes():
    assert check_meal_limit(rec()) == []


def test_expensive_meal_flagged():
    assert check_meal_limit(rec(amount="900", attendees="2"))


def test_entertainment_flagged():
    assert check_entertainment(rec(venue="Golf club"))[0]["severity"] == "HIGH"


def test_fee_within_fmv_passes():
    assert check_fair_market_value(rec(nature_of_payment="Speaker Fee", amount="600", hours="3")) == []


def test_fee_above_fmv_flagged():
    assert check_fair_market_value(rec(nature_of_payment="Speaker Fee", amount="6000", hours="2"))


def test_gift_flagged():
    assert check_gifts(rec(nature_of_payment="Gift", amount="10"))


def test_missing_npi_flagged():
    assert check_sunshine_fields(rec(hcp_npi=""))


def test_meal_frequency_flagged():
    records = [rec(record_id=f"T{i}", date=f"2026-08-{i + 1:02d}") for i in range(6)]
    assert len(check_meal_frequency(records)) == 6
