"""Service for analyzing and extracting company information from job postings."""

from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from backend.models.company import Company
import re
from backend.data.skills import load_skills_database

# Load skills database
SKILLS_DB = load_skills_database()
KNOWN_SKILLS = set(skill['name'].lower() for skill in SKILLS_DB)


def extract_company_info(job_data: Dict) -> Dict:
    """Extract company insights from a single job posting.
    
    Args:
        job_data: Dict with 'company', 'title', 'jd' keys
    
    Returns:
        Dict with extracted: roles, tech_stack, locations, salary, industry
    """
    
    company_name = job_data.get('company', '').strip()
    jd = job_data.get('jd', '').lower()
    title = job_data.get('title', '').lower()
    
    return {
        "roles": extract_roles_from_jd(title, jd),
        "tech_stack": extract_tech_from_jd(jd),
        "locations": extract_locations_from_jd(jd),
        "salary": extract_salary_from_jd(jd),
        "industry": infer_industry(company_name, jd),
    }


def extract_roles_from_jd(title: str, jd: str) -> List[str]:
    """Extract job roles mentioned in JD."""
    
    roles = []
    
    # Common roles in tech
    role_patterns = {
        "Software Engineer": r"software engineer|sde|developer",
        "Frontend Developer": r"frontend|ui\/ux|react|angular|vue",
        "Backend Developer": r"backend|server|api|microservice",
        "DevOps Engineer": r"devops|ci\/cd|infrastructure|kubernetes|docker",
        "Data Engineer": r"data engineer|etl|pipeline|spark",
        "Mobile Developer": r"mobile|ios|android|react native",
        "QA Engineer": r"qa|quality assurance|test engineer",
        "Product Manager": r"product manager|pm",
        "Solutions Architect": r"solutions architect|architect",
        "Database Administrator": r"database|dba|sql",
    }
    
    combined_text = f"{title} {jd}"
    
    for role, pattern in role_patterns.items():
        if re.search(pattern, combined_text):
            roles.append(role)
    
    return list(set(roles)) if roles else ["Software Engineer"]


def extract_tech_from_jd(jd: str) -> List[str]:
    """Extract technology stack from JD using skill database."""
    
    tech_stack: Set[str] = set()
    jd_lower = jd.lower()
    
    # Search for known skills
    for skill in SKILLS_DB:
        skill_name_lower = skill['name'].lower()
        if skill_name_lower in jd_lower:
            tech_stack.add(skill['name'])
    
    # Add regex patterns for common tech
    tech_patterns = {
        "Java": r"\bjava\b",
        "Python": r"\bpython\b",
        "JavaScript": r"\bjavascript\b|\bjs\b",
        "TypeScript": r"\btypescript\b",
        "React": r"\breact\b",
        "Vue": r"\bvue\b",
        "Angular": r"\bangular\b",
        "Node.js": r"\bnode\.?js\b",
        "Express": r"\bexpress\b",
        "Django": r"\bdjango\b",
        "Flask": r"\bflask\b",
        "FastAPI": r"\bfastapi\b",
        "Docker": r"\bdocker\b",
        "Kubernetes": r"\bkubernetes\b|k8s",
        "AWS": r"\baws\b|amazon web services",
        "Azure": r"\bazure\b",
        "GCP": r"\bgcp\b|google cloud",
        "SQL": r"\bsql\b",
        "PostgreSQL": r"\bpostgres\b",
        "MySQL": r"\bmysql\b",
        "MongoDB": r"\bmongodb\b",
        "Redis": r"\bredis\b",
        "Elasticsearch": r"\belasticsearch\b",
        "Kafka": r"\bkafka\b",
        "RabbitMQ": r"\brabbitmq\b",
        "Git": r"\bgit\b",
        "CI/CD": r"\bci\/cd\b|ci cd|continuous integration",
        "Jenkins": r"\bjenkins\b",
        "Terraform": r"\bterraform\b",
        "Microservices": r"\bmicroservice\b",
        "REST API": r"\brest api\b|restful",
        "GraphQL": r"\bgraphql\b",
    }
    
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, jd_lower):
            tech_stack.add(tech)
    
    return sorted(list(tech_stack))


def extract_locations_from_jd(jd: str) -> List[str]:
    """Extract location information from JD."""
    
    locations = []
    
    # Common Indian cities for tech
    city_patterns = {
        "Bangalore": r"bangalore|bengaluru|blr",
        "Hyderabad": r"hyderabad|hyd",
        "Pune": r"pune",
        "Mumbai": r"mumbai|bombay",
        "Delhi": r"delhi|delhi|new delhi",
        "Chennai": r"chennai|madras",
        "Gurgaon": r"gurgaon|gurugram",
        "Noida": r"noida",
        "Kolkata": r"kolkata|calcutta",
        "Remote": r"remote|work from home|wfh",
        "On-site": r"on-site|on site|office",
    }
    
    jd_lower = jd.lower()
    
    for location, pattern in city_patterns.items():
        if re.search(pattern, jd_lower):
            locations.append(location)
    
    return locations or ["Remote/On-site"]


def extract_salary_from_jd(jd: str) -> Optional[str]:
    """Extract salary information from JD."""
    
    # Pattern for INR salary
    inr_pattern = r"[₹]?\s*(\d+\.?\d*)\s*(?:L|Lakh|lakhs|crore|Cr)"
    
    matches = re.findall(inr_pattern, jd, re.IGNORECASE)
    
    if matches:
        return f"₹{matches[0]}L"
    
    # Pattern for dollar amounts
    usd_pattern = r"\$\s*(\d+(?:,\d+)?(?:\.\d+)?)"
    matches = re.findall(usd_pattern, jd)
    
    if matches:
        return f"${matches[0]}"
    
    return None


def infer_industry(company_name: str, jd: str) -> Optional[str]:
    """Infer industry/domain from company name and JD."""
    
    jd_lower = jd.lower()
    
    industry_keywords = {
        "Finance": ["bank", "fintech", "payment", "trading", "insurance"],
        "Healthcare": ["hospital", "health", "medical", "pharma", "clinical"],
        "Retail": ["ecommerce", "retail", "shopping", "marketplace"],
        "Energy": ["energy", "power", "utility", "oil", "gas", "siemens emeter"],
        "Manufacturing": ["manufacturing", "production", "industrial", "automation"],
        "Telecom": ["telecom", "communication", "network", "5g"],
        "Education": ["education", "edtech", "learning"],
        "Automotive": ["automotive", "vehicle", "tesla", "tata"],
        "Media": ["media", "entertainment", "streaming"],
    }
    
    for industry, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword in jd_lower or keyword in company_name.lower():
                return industry
    
    return "Technology"


def get_or_create_company(db: Session, company_name: str) -> Company:
    """Get existing company or create new one."""
    
    company = db.query(Company).filter(
        Company.name.ilike(company_name)
    ).first()
    
    if not company:
        company = Company(
            name=company_name,
            industry="Technology",  # Default
            jobs_analyzed=0
        )
        db.add(company)
        db.flush()
    
    return company


def analyze_company_profile(companies_list: List[Dict]) -> Dict:
    """Analyze multiple job postings to build company profile.
    
    Args:
        companies_list: List of job posting dicts with company info
    
    Returns:
        Aggregated company profile
    """
    
    all_roles: Set[str] = set()
    all_tech: Set[str] = set()
    all_locations: Set[str] = set()
    salary_data: List[str] = []
    industries: Set[str] = set()
    
    for job in companies_list:
        info = extract_company_info(job)
        all_roles.update(info.get("roles", []))
        all_tech.update(info.get("tech_stack", []))
        all_locations.update(info.get("locations", []))
        
        if info.get("salary"):
            salary_data.append(info["salary"])
        
        if info.get("industry"):
            industries.add(info["industry"])
    
    return {
        "roles": sorted(list(all_roles)),
        "tech_stack": sorted(list(all_tech)),
        "locations": sorted(list(all_locations)),
        "industries": sorted(list(industries)),
        "salary_range": f"{salary_data[0]} - {salary_data[-1]}" if salary_data else None,
        "jobs_analyzed": len(companies_list),
    }
