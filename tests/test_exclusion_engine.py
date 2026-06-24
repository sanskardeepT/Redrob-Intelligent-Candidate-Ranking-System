import pytest
from src.exclusion_engine import (
    excl_research_only,
    excl_consulting_only,
    excl_cv_speech_robotics_only,
    excl_location_visa,
    excl_title_chaser,
    excl_stale_architect,
    run_exclusions
)

def test_excl_research_only():
    # Case 1: Excluded (no production keywords)
    cand_excluded = {
        "career_history": [
            {"industry": "Research Lab", "description": "Researched deep learning papers and wrote theoretical formulations."}
        ]
    }
    excluded, reason = excl_research_only(cand_excluded)
    assert excluded
    assert "Research only" in reason

    # Case 2: Not excluded (has "deployed" and "users")
    cand_clean = {
        "career_history": [
            {"industry": "Software", "description": "Deployed ML model to production for 10k users."}
        ]
    }
    excluded, reason = excl_research_only(cand_clean)
    assert not excluded


def test_excl_consulting_only():
    # Case 1: Excluded (only worked at TCS and Infosys)
    cand_excluded = {
        "career_history": [
            {"company": "TCS"},
            {"company": "Infosys Technologies"}
        ]
    }
    excluded, reason = excl_consulting_only(cand_excluded)
    assert excluded
    assert "Consulting only" in reason

    # Case 2: Not excluded (worked at TCS, then Google)
    cand_clean = {
        "career_history": [
            {"company": "TCS"},
            {"company": "Google"}
        ]
    }
    excluded, reason = excl_consulting_only(cand_clean)
    assert not excluded


def test_excl_cv_speech_robotics_only():
    # Case 1: Excluded (has CV terms, no NLP terms)
    cand_excluded = {
        "profile": {"current_industry": "Computer Vision"},
        "career_history": [
            {"description": "Developed object detection model using YOLO and image segmentation."}
        ]
    }
    excluded, reason = excl_cv_speech_robotics_only(cand_excluded)
    assert excluded
    assert "CV/Speech/Robotics only" in reason

    # Case 2: Not excluded (has CV terms but also LLMs/retrieval)
    cand_clean = {
        "profile": {"current_industry": "Computer Vision"},
        "career_history": [
            {"description": "Developed object detection and hybrid search for vector database."}
        ]
    }
    excluded, reason = excl_cv_speech_robotics_only(cand_clean)
    assert not excluded


def test_excl_location_visa():
    # Case 1: Excluded (USA, unwilling to relocate)
    cand_excluded = {
        "profile": {"country": "USA"},
        "redrob_signals": {"willing_to_relocate": False}
    }
    excluded, reason = excl_location_visa(cand_excluded)
    assert excluded
    assert "Location/Visa restriction" in reason

    # Case 2: Not excluded (USA, willing to relocate)
    cand_clean = {
        "profile": {"country": "USA"},
        "redrob_signals": {"willing_to_relocate": True}
    }
    excluded, reason = excl_location_visa(cand_clean)
    assert not excluded

    # Case 3: Not excluded (India, unwilling to relocate)
    cand_clean_india = {
        "profile": {"country": "India"},
        "redrob_signals": {"willing_to_relocate": False}
    }
    excluded, reason = excl_location_visa(cand_clean_india)
    assert not excluded


def test_excl_title_chaser():
    # Case 1: Excluded (escalation Senior -> Staff -> Principal, mean duration < 18m)
    cand_excluded = {
        "career_history": [
            {"title": "Senior Software Engineer", "duration_months": 12, "start_date": "2020-01-01"},
            {"title": "Staff Engineer", "duration_months": 12, "start_date": "2021-01-01"},
            {"title": "Principal Architect", "duration_months": 12, "start_date": "2022-01-01"}
        ]
    }
    excluded, reason = excl_title_chaser(cand_excluded)
    assert excluded
    assert "Title chaser" in reason

    # Case 2: Not excluded (escalation but long tenure)
    cand_clean_duration = {
        "career_history": [
            {"title": "Senior Software Engineer", "duration_months": 24, "start_date": "2020-01-01"},
            {"title": "Staff Engineer", "duration_months": 24, "start_date": "2022-01-01"},
            {"title": "Principal Architect", "duration_months": 24, "start_date": "2024-01-01"}
        ]
    }
    excluded, reason = excl_title_chaser(cand_clean_duration)
    assert not excluded

    # Case 3: Not excluded (short tenure but flat title progression)
    cand_clean_progression = {
        "career_history": [
            {"title": "Senior Software Engineer", "duration_months": 12, "start_date": "2020-01-01"},
            {"title": "Senior Software Engineer", "duration_months": 12, "start_date": "2021-01-01"}
        ]
    }
    excluded, reason = excl_title_chaser(cand_clean_progression)
    assert not excluded


def test_excl_stale_architect():
    # Case 1: Excluded (Tech Lead, >18 months, no hands-on keywords)
    cand_excluded = {
        "career_history": [
            {
                "title": "Tech Lead",
                "duration_months": 24,
                "is_current": True,
                "description": "Managed sprint planning meetings, coordinated with stakeholders, and oversaw resources."
            }
        ]
    }
    excluded, reason = excl_stale_architect(cand_excluded)
    assert excluded
    assert "Stale architect" in reason

    # Case 2: Not excluded (Tech Lead, >18 months, has "python" and "develop")
    cand_clean_hands_on = {
        "career_history": [
            {
                "title": "Tech Lead",
                "duration_months": 24,
                "is_current": True,
                "description": "Led team and did python coding to develop core backend models."
            }
        ]
    }
    excluded, reason = excl_stale_architect(cand_clean_hands_on)
    assert not excluded


def test_run_exclusions_clean():
    # A candidate passing all rules
    candidate = {
        "profile": {"country": "India"},
        "redrob_signals": {"willing_to_relocate": False},
        "career_history": [
            {
                "company": "Google",
                "title": "Senior Software Engineer",
                "duration_months": 36,
                "is_current": True,
                "industry": "Internet",
                "description": "Developed and deployed core ranking algorithms for search to production serving users."
            }
        ]
    }
    reasons = run_exclusions(candidate)
    assert len(reasons) == 0
