"""
Hard Exclusion Engine module.
Applies strict job description (JD) derived disqualifiers to filter candidates.
Each rule is a separate function to be independently testable and explainable.
"""
import re
from typing import Dict, Any, Tuple, List

# Rule 1 Constants
PRODUCTION_KEYWORDS = {
    "user", "users", "scale", "production", "shipped", "deployed", "pipeline", 
    "inference", "dataset", "model", "api", "service", "system", "dashboard", 
    "fine-tuned", "trained", "serving", "real-time", "end-to-end"
}

# Rule 6 Constants
HANDS_ON_KEYWORDS = {
    "code", "coding", "programming", "implement", "implemented", "implementing",
    "develop", "developing", "developed", "write", "writing", "wrote", "build",
    "building", "built", "train", "training", "trained", "fine-tune", "finetuning",
    "fine-tuning", "optimize", "optimizing", "optimized", "python", "pytorch",
    "tensorflow", "github", "git", "scikit-learn", "numpy", "pandas"
}


def excl_research_only(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates whose career history shows no evidence of production deployment.
    Requires at least one mention of production keywords.
    """
    career_history = candidate.get("career_history", [])
    if not career_history:
        return True, "No career history records available."

    combined_text = ""
    for role in career_history:
        combined_text += f" {role.get('industry', '')} {role.get('description', '')}"

    combined_text_lower = combined_text.lower()
    
    # Check if any production keyword is present
    has_production_evidence = any(word in combined_text_lower for word in PRODUCTION_KEYWORDS)
    
    if not has_production_evidence:
        return True, "Research only: Career history contains no evidence of production deployment."
    
    return False, ""


def excl_consulting_only(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates who have only worked at major IT services/consulting firms:
    {TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini}.
    Triggered only if ALL employers in their history are in this set.
    """
    career_history = candidate.get("career_history", [])
    if not career_history:
        return False, ""

    services_firms = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "tata consultancy services"}
    
    all_consulting = True
    for role in career_history:
        company = role.get("company", "").strip().lower()
        # Check if the company name contains or matches any services firm
        is_service = any(firm in company for firm in services_firms)
        if not is_service:
            all_consulting = False
            break

    if all_consulting:
        return True, "Consulting only: All listed employers are services firms (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini) without non-services experience."
    
    return False, ""


def excl_cv_speech_robotics_only(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates whose experience is dominated by CV/Speech/Robotics with no NLP/IR skills.
    Checks the structured skills array:
    - Excluded if candidate has CV-specific named skills.
    - AND no NLP/IR-specific named skill with duration_months > 0.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return False, ""

    cv_keywords = ["computer vision", "opencv", "yolo", "image segmentation"]
    nlp_keywords = [
        "nlp", "bert", "transformer", "embeddings", "retrieval", "vector database", 
        "elasticsearch", "faiss", "pinecone"
    ]
    
    has_cv_skill = False
    has_nlp_skill = False
    
    for skill in skills:
        name_lower = skill.get("name", "").lower()
        duration = skill.get("duration_months", 0)
        
        # Check CV skills (substring match)
        if any(kw in name_lower for kw in cv_keywords):
            has_cv_skill = True
            
        # Check NLP skills with duration_months > 0 (substring match)
        if any(kw in name_lower for kw in nlp_keywords) and duration > 0:
            has_nlp_skill = True
            
    if has_cv_skill and not has_nlp_skill:
        return True, "CV/Speech/Robotics only: Candidate has CV-specific skills but no NLP/IR-specific skills with duration > 0."
        
    return False, ""


def excl_location_visa(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates who are located outside India AND unwilling to relocate.
    (JD: open to Tier-1 India cities + relocation, no visa sponsorship.)
    """
    profile = candidate.get("profile", {})
    country = profile.get("country", "").strip().lower()
    
    redrob_signals = candidate.get("redrob_signals", {})
    willing_to_relocate = redrob_signals.get("willing_to_relocate", False)

    if country != "india" and not willing_to_relocate:
        return True, f"Location/Visa restriction: Located in '{country}' and unwilling to relocate to India."
        
    return False, ""


def get_title_seniority(title: str) -> int:
    """Helper to score title seniority for title chaser detection."""
    title_lower = title.lower()
    
    # Ordered levels (higher is more senior)
    if any(word in title_lower for word in ["principal", "director", "vp", "chief", "head"]):
        return 4
    if any(word in title_lower for word in ["staff", "lead", "manager"]):
        return 3
    if any(word in title_lower for word in ["senior", "sr", "sr."]):
        return 2
    if any(word in title_lower for word in ["engineer", "developer", "member", "associate", "analyst"]):
        return 1
    return 1


def excl_title_chaser(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates with rapid promotions/seniority escalation but short tenures.
    Rule:
    - Looks at last 3 roles (if available) chronologically.
    - Mean duration_months < 18.
    - Titles show Senior -> Staff -> Principal style escalation pattern.
    """
    career_history = candidate.get("career_history", [])
    if not career_history:
        return False, ""

    # Sort roles chronologically (oldest first)
    # Parse dates or assume list order, but let's sort by start_date to be robust.
    # Note: candidates.jsonl usually has career history sorted newest first or oldest first.
    # Let's sort by start_date ascending.
    sorted_history = sorted(
        career_history, 
        key=lambda x: x.get("start_date", "")
    )
    
    # Get last 3 roles
    last_roles = sorted_history[-3:]
    if len(last_roles) < 2:
        return False, "" # Need at least 2 roles to determine escalation

    mean_duration = sum(r.get("duration_months", 0) for r in last_roles) / len(last_roles)
    
    if mean_duration >= 18.0:
        return False, ""

    # Check for escalation pattern: ranks of roles are strictly increasing
    ranks = [get_title_seniority(r.get("title", "")) for r in last_roles]
    
    # Escalation: ranks are non-decreasing and have at least one increase
    has_escalation = all(ranks[i] <= ranks[i+1] for i in range(len(ranks) - 1)) and ranks[-1] > ranks[0]
    
    if has_escalation:
        ranks_str = " -> ".join(map(str, ranks))
        return True, f"Title chaser: Mean duration of last roles is {mean_duration:.1f} months (< 18) with escalation pattern ({ranks_str})."
        
    return False, ""


def excl_stale_architect(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates currently in management/architect roles who have lost touch with hands-on work.
    Rule:
    - Current title contains "Architect", "Tech Lead", or "Head of".
    - Current role description contains NO hands-on/code keywords.
    - Current role duration > 18 months.
    """
    career_history = candidate.get("career_history", [])
    current_role = None
    for role in career_history:
        if role.get("is_current", False):
            current_role = role
            break
            
    if not current_role:
        return False, ""

    title = current_role.get("title", "")
    title_lower = title.lower()
    
    is_architect_lead = any(word in title_lower for word in ["architect", "tech lead", "head of"])
    if not is_architect_lead:
        return False, ""

    duration = current_role.get("duration_months", 0)
    if duration <= 18:
        return False, ""

    description = current_role.get("description", "").lower()
    has_hands_on = any(word in description for word in HANDS_ON_KEYWORDS)

    if not has_hands_on:
        return True, f"Stale architect: Title '{title}' for {duration} months with no hands-on keywords in description."
        
    return False, ""


def run_exclusions(candidate: Dict[str, Any]) -> List[str]:
    """
    Runs all six exclusion rules on a candidate.
    Returns:
        List[str]: List of all triggered exclusion reason strings. Empty if clean.
    """
    reasons = []
    
    rules = [
        excl_research_only,
        excl_consulting_only,
        excl_cv_speech_robotics_only,
        excl_location_visa,
        excl_title_chaser,
        excl_stale_architect
    ]
    
    for rule in rules:
        excluded, reason = rule(candidate)
        if excluded:
            reasons.append(reason)
            
    return reasons
