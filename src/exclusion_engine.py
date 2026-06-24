"""
Hard Exclusion Engine module.
Applies strict job description (JD) derived disqualifiers to filter candidates.
Each rule is a separate function to be independently testable and explainable.
"""
import re
from typing import Dict, Any, Tuple, List

# Rule 1 Constants
PRODUCTION_KEYWORDS = {"user", "users", "scale", "production", "shipped", "deployed"}

# Rule 3 Constants
CV_SPEECH_ROBOTICS_KEYWORDS = {
    "computer vision", "cv", "object detection", "image segmentation", "yolo",
    "speech recognition", "speech-to-text", "text-to-speech", "asr", "tts",
    "robotics", "slam", "lidar", "autonomous vehicle", "autonomous vehicles",
    "image classification", "segmentation", "ros"
}

NLP_IR_RETRIEVAL_KEYWORDS = {
    "nlp", "natural language processing", "information retrieval", "retrieval",
    "search engine", "vector database", "vector search", "llm", "large language model",
    "embeddings", "milvus", "qdrant", "pinecone", "chroma", "faiss", "elasticsearch",
    "solr", "lucene", "bert", "transformer", "hybrid search", "ndcg", "mrr", "map",
    "recommender", "recommendation"
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
    Requires at least one mention of production keywords (users, scale, production, shipped, deployed).
    
    Why these keywords?
    - 'users': Indicates the candidate builds software that actual people interact with.
    - 'scale': Demonstrates experience handling large volume or high traffic.
    - 'production': Directly indicates deployment in live environments.
    - 'shipped': Represents completing and delivering software features/products.
    - 'deployed': Reflects the operationalization of models or software systems.
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
        return True, "Research only: Career history contains no evidence of production deployment (users, scale, production, shipped, deployed)."
    
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


# Compiled Regexes for fast matching
CV_SPEECH_ROBOTICS_REGEX = re.compile(
    r'\b(' + '|'.join(map(re.escape, CV_SPEECH_ROBOTICS_KEYWORDS)) + r')\b',
    re.IGNORECASE
)
NLP_IR_RETRIEVAL_REGEX = re.compile(
    r'\b(' + '|'.join(map(re.escape, NLP_IR_RETRIEVAL_KEYWORDS)) + r')\b',
    re.IGNORECASE
)


def excl_cv_speech_robotics_only(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Excludes candidates whose experience is dominated by Computer Vision, Speech, or Robotics 
    with zero NLP, Information Retrieval, or Vector Search experience.
    
    Rule:
    - Counts of CV/Speech/Robotics keywords in current_industry and career description is > 0.
    - NLP/IR/Retrieval keyword count is exactly 0.
    """
    profile = candidate.get("profile", {})
    current_industry = profile.get("current_industry", "").lower()
    
    career_history = candidate.get("career_history", [])
    combined_text = current_industry
    for role in career_history:
        combined_text += f" {role.get('description', '')}"
    
    combined_text_lower = combined_text.lower()

    # Search for occurrences using precompiled regexes
    cv_count = len(CV_SPEECH_ROBOTICS_REGEX.findall(combined_text_lower))
    nlp_count = len(NLP_IR_RETRIEVAL_REGEX.findall(combined_text_lower))

    if cv_count > 0 and nlp_count == 0:
        return True, f"CV/Speech/Robotics only: Profile contains CV/Speech/Robotics terms ({cv_count}) but 0 NLP/IR/Retrieval terms."
        
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
