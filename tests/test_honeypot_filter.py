import pytest
from src.honeypot_filter import is_honeypot

def test_clean_candidate():
    candidate = {
        "candidate_id": "CAND_0000001",
        "profile": {
            "years_of_experience": 5.0
        },
        "career_history": [
            {"duration_months": 24},
            {"duration_months": 36}
        ],
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 48},
            {"name": "SQL", "proficiency": "intermediate", "duration_months": 0}
        ]
    }
    is_hp, reasons = is_honeypot(candidate)
    assert not is_hp
    assert len(reasons) == 0

def test_experience_mismatch_honeypot():
    # 5 years declared, but only 12 months (1 year) in career history
    candidate = {
        "candidate_id": "CAND_0000002",
        "profile": {
            "years_of_experience": 5.0
        },
        "career_history": [
            {"duration_months": 12}
        ],
        "skills": []
    }
    is_hp, reasons = is_honeypot(candidate)
    assert is_hp
    assert any("Experience mismatch" in r for r in reasons)

def test_zero_duration_expert_honeypot():
    candidate = {
        "candidate_id": "CAND_0000003",
        "profile": {
            "years_of_experience": 2.0
        },
        "career_history": [
            {"duration_months": 24}
        ],
        "skills": [
            {"name": "Machine Learning", "proficiency": "expert", "duration_months": 0}
        ]
    }
    is_hp, reasons = is_honeypot(candidate)
    assert is_hp
    assert any("Zero-duration expert skill" in r for r in reasons)

def test_multiple_honeypot_triggers():
    candidate = {
        "candidate_id": "CAND_0000004",
        "profile": {
            "years_of_experience": 10.0
        },
        "career_history": [
            {"duration_months": 24} # 2 years
        ],
        "skills": [
            {"name": "PyTorch", "proficiency": "expert", "duration_months": 0}
        ]
    }
    is_hp, reasons = is_honeypot(candidate)
    assert is_hp
    assert len(reasons) == 2
