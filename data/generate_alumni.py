"""
Synthetic Alumni Data Generator
Generates 500 realistic alumni records with diverse career trajectories.
"""
import csv
import random
import re
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALUMNI_CSV_PATH, DATA_DIR

# --- Name Pools ---
FIRST_NAMES_MALE = [
    "Aarav", "Arjun", "Rohan", "Vikram", "Siddharth", "Aditya", "Karthik",
    "Rahul", "Nikhil", "Pranav", "Devesh", "Harish", "Manish", "Suresh",
    "Ramesh", "Akash", "Varun", "Tarun", "Gaurav", "Sahil", "Ankit",
    "Deepak", "Vishal", "Rajesh", "Amit", "Kunal", "Vivek", "Ashwin",
    "Neeraj", "Shreyas", "Abhinav", "Ishaan", "Dhruv", "Yash", "Arnav",
    "Lakshya", "Parth", "Rishi", "Kabir", "Shaurya", "Om", "Advait",
    "Reyansh", "Atharv", "Vihaan", "Ayaan", "Krishna", "Aakash", "Tushar", "Jay"
]

FIRST_NAMES_FEMALE = [
    "Priya", "Ananya", "Sneha", "Kavya", "Meera", "Neha", "Divya",
    "Pooja", "Sakshi", "Tanvi", "Isha", "Riya", "Nisha", "Shruti",
    "Aditi", "Swati", "Pallavi", "Rashmi", "Anjali", "Kriti", "Simran",
    "Aishwarya", "Bhavna", "Deepika", "Harini", "Lakshmi", "Megha",
    "Nikita", "Preeti", "Radhika", "Sanya", "Trisha", "Urvi", "Vidya",
    "Zara", "Anika", "Diya", "Gauri", "Jiya", "Kiara", "Mira",
    "Nandini", "Pari", "Rhea", "Saanvi", "Tara", "Vanya", "Arya", "Myra", "Sara"
]

LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Reddy", "Joshi",
    "Mehta", "Shah", "Nair", "Iyer", "Rao", "Desai", "Chopra",
    "Malhotra", "Bhatia", "Kapoor", "Verma", "Saxena", "Agarwal",
    "Mishra", "Pandey", "Tiwari", "Trivedi", "Banerjee", "Mukherjee",
    "Chatterjee", "Das", "Bose", "Sen", "Hegde", "Kulkarni", "Patil",
    "Deshpande", "Menon", "Pillai", "Krishnan", "Subramaniam", "Venkatesh",
    "Srinivasan", "Rajan", "Mahajan", "Khanna", "Bajaj", "Sethi",
    "Arora", "Dhawan", "Kaul", "Chandra", "Bhatt"
]

# --- Department & Skills ---
DEPARTMENTS = [
    "Computer Science", "Electronics & Communication", "Mechanical Engineering",
    "Electrical Engineering", "Information Technology", "Civil Engineering",
    "Chemical Engineering", "Biotechnology"
]

SKILLS_BY_DEPT = {
    "Computer Science": [
        "Python", "Java", "Machine Learning", "Deep Learning", "React",
        "Node.js", "TensorFlow", "PyTorch", "Docker", "Kubernetes",
        "AWS", "SQL", "MongoDB", "REST APIs", "Microservices",
        "Natural Language Processing", "Computer Vision", "Data Structures",
        "System Design", "Go", "Rust", "TypeScript", "GraphQL",
        "Redis", "Kafka", "CI/CD", "Git", "Linux", "Algorithms"
    ],
    "Electronics & Communication": [
        "VLSI Design", "Embedded Systems", "Signal Processing", "MATLAB",
        "PCB Design", "IoT", "Verilog", "ARM Architecture", "FPGA",
        "Wireless Communication", "Python", "C++", "Antenna Design",
        "RF Engineering", "Sensor Networks", "Robotics", "Control Systems"
    ],
    "Mechanical Engineering": [
        "AutoCAD", "SolidWorks", "ANSYS", "CATIA", "3D Printing",
        "FEA", "CFD", "Manufacturing", "Thermodynamics", "Robotics",
        "Python", "Project Management", "Six Sigma", "Lean Manufacturing",
        "Supply Chain", "Quality Control", "CNC Programming"
    ],
    "Electrical Engineering": [
        "Power Systems", "Control Systems", "MATLAB", "PLC Programming",
        "SCADA", "Renewable Energy", "Circuit Design", "Transformers",
        "Electrical Machines", "Python", "IoT", "Smart Grid",
        "Power Electronics", "Embedded Systems", "Automation"
    ],
    "Information Technology": [
        "Python", "JavaScript", "React", "Angular", "Node.js",
        "Cloud Computing", "AWS", "Azure", "DevOps", "Docker",
        "Cybersecurity", "Networking", "SQL", "NoSQL", "Agile",
        "Scrum", "UI/UX Design", "Mobile Development", "Flutter",
        "Data Analytics", "Tableau", "Power BI"
    ],
    "Civil Engineering": [
        "AutoCAD", "STAAD Pro", "Revit", "Structural Analysis",
        "Concrete Technology", "Surveying", "Project Management",
        "Construction Management", "BIM", "Quantity Estimation",
        "Geotechnical Engineering", "Environmental Engineering",
        "Python", "GIS", "Water Resources"
    ],
    "Chemical Engineering": [
        "Process Design", "ASPEN Plus", "Chemical Kinetics",
        "Process Simulation", "Quality Control", "Environmental Engineering",
        "MATLAB", "Python", "Thermodynamics", "Catalysis",
        "Polymer Science", "Pharmaceutical Engineering", "R&D",
        "Data Analysis", "Six Sigma"
    ],
    "Biotechnology": [
        "Bioinformatics", "Genomics", "PCR", "Molecular Biology",
        "Cell Culture", "Protein Engineering", "CRISPR", "Python",
        "R", "Machine Learning", "Drug Discovery", "Clinical Trials",
        "Biostatistics", "Immunology", "Microbiology", "Biochemistry"
    ]
}

# --- Companies ---
TECH_GIANTS = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix",
    "Adobe", "Salesforce", "Oracle", "Intel", "NVIDIA", "IBM"
]

INDIAN_IT = [
    "Infosys", "TCS", "Wipro", "HCL Technologies", "Tech Mahindra",
    "Cognizant", "Mindtree", "Mphasis", "LTIMindtree", "Persistent Systems"
]

STARTUPS = [
    "Flipkart", "Razorpay", "Zerodha", "CRED", "Swiggy", "Zomato",
    "PhonePe", "Meesho", "Groww", "Unacademy", "Byju's", "Ola",
    "ShareChat", "Postman", "BrowserStack", "Freshworks", "Chargebee",
    "Zoho", "Hasura", "DeepSource", "Atlan", "Yellow.ai", "Fractal Analytics"
]

CONSULTING = [
    "McKinsey", "BCG", "Bain & Company", "Deloitte", "Accenture",
    "PwC", "Ernst & Young", "KPMG"
]

RESEARCH_LABS = [
    "Google Research", "Microsoft Research", "DeepMind", "OpenAI",
    "ISRO", "DRDO", "IISc Research", "IBM Research", "NVIDIA Research"
]

FINANCE = [
    "Goldman Sachs", "Morgan Stanley", "JPMorgan Chase", "Deutsche Bank",
    "Barclays", "Citadel", "Tower Research Capital", "WorldQuant"
]

PRODUCT_COMPANIES = [
    "Atlassian", "Spotify", "Uber", "Airbnb", "Stripe", "Twilio",
    "Slack", "GitHub", "Shopify", "Notion"
]

ALL_COMPANIES = TECH_GIANTS + INDIAN_IT + STARTUPS + CONSULTING + RESEARCH_LABS + FINANCE + PRODUCT_COMPANIES

# --- Roles ---
ROLES_BY_CAREER = {
    "software_engineer": [
        "Software Engineer", "Senior Software Engineer", "Staff Engineer",
        "Principal Engineer", "Software Developer", "Backend Developer",
        "Full Stack Developer", "Frontend Engineer", "Senior SDE",
        "SDE-II", "SDE-III", "Engineering Lead"
    ],
    "data_science": [
        "Data Scientist", "Senior Data Scientist", "Lead Data Scientist",
        "ML Engineer", "Machine Learning Engineer", "Senior ML Engineer",
        "AI Engineer", "Deep Learning Engineer", "Applied Scientist",
        "Research Scientist", "Data Analyst", "Analytics Engineer"
    ],
    "product": [
        "Product Manager", "Senior Product Manager", "Associate Product Manager",
        "Group Product Manager", "Director of Product", "Product Analyst",
        "Technical Product Manager"
    ],
    "research": [
        "Research Scientist", "Senior Researcher", "Research Engineer",
        "PhD Researcher", "Postdoctoral Fellow", "Lab Director",
        "Principal Research Scientist"
    ],
    "management": [
        "Engineering Manager", "Senior Engineering Manager", "VP Engineering",
        "CTO", "Director of Engineering", "Tech Lead Manager"
    ],
    "entrepreneur": [
        "Founder & CEO", "Co-Founder", "CTO & Co-Founder",
        "Founder", "CEO", "Technical Co-Founder"
    ],
    "consulting": [
        "Management Consultant", "Senior Consultant", "Associate",
        "Business Analyst", "Strategy Consultant", "Technology Consultant"
    ],
    "domain_engineer": [
        "VLSI Design Engineer", "Embedded Systems Engineer", "Mechanical Design Engineer",
        "Process Engineer", "Structural Engineer", "Biotech Researcher",
        "Hardware Engineer", "Control Systems Engineer", "Power Systems Engineer",
        "Environmental Engineer", "Quality Engineer"
    ]
}

# --- Locations ---
INDIAN_CITIES = [
    "Bangalore", "Hyderabad", "Mumbai", "Pune", "Chennai",
    "Delhi NCR", "Gurgaon", "Noida", "Kolkata", "Ahmedabad",
    "Kochi", "Jaipur", "Chandigarh", "Indore", "Coimbatore"
]

GLOBAL_CITIES = [
    "San Francisco", "New York", "Seattle", "London", "Singapore",
    "Toronto", "Berlin", "Tokyo", "Dublin", "Amsterdam"
]

ALL_LOCATIONS = INDIAN_CITIES * 3 + GLOBAL_CITIES  # Indian cities weighted higher

# --- Mentor IDs ---
MENTOR_NAMES = [
    "Dr. Sharma", "Dr. Patel", "Dr. Raghavan", "Dr. Iyer",
    "Dr. Reddy", "Dr. Gupta", "Dr. Nair", "Dr. Kulkarni",
    "Dr. Banerjee", "Dr. Mehta", "Dr. Joshi", "Dr. Subramaniam",
    "Dr. Krishnamurthy", "Dr. Desai", "Dr. Venkatesh", "Dr. Chakraborty",
    "Prof. Singh", "Prof. Kapoor", "Prof. Malhotra", "Prof. Mishra"
]

# --- Bio Templates ---
BIO_TEMPLATES = [
    "Passionate about {interest1} and {interest2}. Previously worked on {project} at {prev_company}. Loves mentoring junior engineers.",
    "Building scalable {interest1} systems. {years}+ years of experience in {interest2}. Open source contributor.",
    "Focused on solving real-world problems using {interest1}. Background in {interest2}. Active tech community speaker.",
    "{interest1} enthusiast with a knack for {interest2}. Transitioned from {prev_role} to pursue passion in technology.",
    "Driven by curiosity in {interest1}. Led multiple {interest2} projects. Believes in continuous learning and growth.",
    "Expert in {interest1} with deep experience in {interest2}. Contributed to products used by millions of users.",
    "Bridging the gap between {interest1} and {interest2}. Published research in top-tier conferences.",
    "Entrepreneur at heart. Building products in the {interest1} space. Former {prev_role} at {prev_company}.",
    "Full stack {interest1} professional. Experienced in {interest2} and cloud technologies. Hackathon winner.",
    "Specializing in {interest1} applications. Strong foundation in {interest2}. Passionate about teaching and outreach.",
    "Working at the intersection of {interest1} and {interest2}. Love building things that matter.",
    "Career focused on {interest1}. Transitioned to {interest2} after discovering passion during a side project.",
    "Tech lead with expertise in {interest1}. Mentoring {years}+ engineers. Advocate for diversity in tech.",
    "Data-driven professional focused on {interest1}. Background in {interest2}. Marathon runner and tech blogger.",
    "Innovation-focused engineer building next-gen {interest1} solutions. Deep expertise in {interest2}.",
]

INTERESTS = [
    "artificial intelligence", "machine learning", "deep learning",
    "natural language processing", "computer vision", "robotics",
    "cloud computing", "distributed systems", "blockchain",
    "cybersecurity", "data engineering", "frontend development",
    "mobile applications", "IoT", "edge computing",
    "fintech", "healthtech", "edtech", "sustainability",
    "quantum computing", "AR/VR", "autonomous systems"
]

PREV_COMPANIES_SUBSET = [
    "Google", "Microsoft", "Amazon", "Flipkart", "Infosys",
    "TCS", "Wipro", "Razorpay", "a startup", "a research lab"
]

PREV_ROLES = [
    "software engineer", "data analyst", "researcher",
    "mechanical engineer", "consultant", "teaching assistant",
    "intern", "project lead", "QA engineer"
]

PROJECTS = [
    "real-time recommendation engines", "distributed ML pipelines",
    "scalable microservices", "computer vision systems",
    "NLP chatbots", "IoT sensor networks", "autonomous drones",
    "fintech payment systems", "health monitoring platforms",
    "educational technology tools"
]

MOBILE_PREFIXES = ["98", "97", "96", "95", "94", "93", "91", "89", "88", "87", "86", "79", "78", "77"]


def generate_phone():
    """Generate a plausible Indian mobile number (10 digits, starts with 6-9)."""
    prefix = random.choice(MOBILE_PREFIXES)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+91 {prefix}{suffix[:4]} {suffix[4:]}"


def generate_email(full_name: str, company: str) -> str:
    """Derive a realistic work email from name and company."""
    parts = full_name.lower().split()
    first = re.sub(r'[^a-z]', '', parts[0])
    last  = re.sub(r'[^a-z]', '', parts[-1]) if len(parts) > 1 else ""
    domain_slug = re.sub(r'[^a-z0-9]', '', company.lower())[:12]
    formats = [
        f"{first}.{last}@{domain_slug}.com",
        f"{first[0]}{last}@{domain_slug}.com",
        f"{first}_{last}@{domain_slug}.in",
    ]
    return random.choice(formats)


def generate_bio(dept, skills):
    """Generate a realistic bio for an alumnus."""
    template = random.choice(BIO_TEMPLATES)
    dept_skills = skills if skills else ["technology"]
    interest1 = random.choice(INTERESTS)
    interest2 = random.choice([s for s in dept_skills[:5]] + INTERESTS[:5])
    if interest2 == interest1:
        interest2 = random.choice(INTERESTS)

    bio = template.format(
        interest1=interest1,
        interest2=interest2,
        years=random.randint(2, 8),
        prev_company=random.choice(PREV_COMPANIES_SUBSET),
        prev_role=random.choice(PREV_ROLES),
        project=random.choice(PROJECTS)
    )
    return bio


def generate_career_path(dept, batch_year):
    """Assign a career path with realistic transitions."""
    years_since_grad = 2026 - batch_year

    # Department influences initial career
    if dept in ["Computer Science", "Information Technology"]:
        careers = ["software_engineer"] * 40 + ["data_science"] * 25 + \
                  ["product"] * 10 + ["research"] * 8 + \
                  ["management"] * 7 + ["entrepreneur"] * 5 + ["consulting"] * 5
    elif dept in ["Electronics & Communication"]:
        careers = ["software_engineer"] * 25 + ["domain_engineer"] * 25 + \
                  ["data_science"] * 15 + ["research"] * 15 + \
                  ["product"] * 8 + ["management"] * 7 + ["entrepreneur"] * 5
    elif dept in ["Mechanical Engineering", "Civil Engineering"]:
        careers = ["domain_engineer"] * 35 + ["software_engineer"] * 15 + \
                  ["consulting"] * 15 + ["management"] * 15 + \
                  ["product"] * 10 + ["entrepreneur"] * 10
    elif dept in ["Chemical Engineering", "Biotechnology"]:
        careers = ["domain_engineer"] * 25 + ["research"] * 25 + \
                  ["consulting"] * 15 + ["data_science"] * 15 + \
                  ["management"] * 10 + ["entrepreneur"] * 5 + ["product"] * 5
    else:
        careers = ["software_engineer"] * 30 + ["data_science"] * 20 + \
                  ["domain_engineer"] * 15 + ["consulting"] * 15 + \
                  ["product"] * 10 + ["management"] * 5 + ["entrepreneur"] * 5

    career = random.choice(careers)

    # Some alumni transition careers (especially after 3+ years)
    transitioned = False
    prev_career = None
    if years_since_grad >= 3 and random.random() < 0.20:
        prev_career = career
        transition_map = {
            "software_engineer": ["product", "management", "data_science", "entrepreneur"],
            "data_science": ["product", "management", "research", "entrepreneur"],
            "domain_engineer": ["software_engineer", "product", "management", "consulting"],
            "consulting": ["product", "entrepreneur", "management"],
            "research": ["data_science", "entrepreneur", "management"],
        }
        if career in transition_map:
            career = random.choice(transition_map[career])
            transitioned = True

    # Pick company based on career
    if career == "entrepreneur":
        company = random.choice(STARTUPS + ["Own Startup", "Stealth Startup"])
    elif career == "research":
        company = random.choice(RESEARCH_LABS + TECH_GIANTS[:4])
    elif career == "consulting":
        company = random.choice(CONSULTING)
    elif career in ["software_engineer", "data_science"]:
        company = random.choice(TECH_GIANTS + STARTUPS + PRODUCT_COMPANIES + INDIAN_IT[:3])
    elif career == "management":
        company = random.choice(TECH_GIANTS + STARTUPS + PRODUCT_COMPANIES)
    elif career == "product":
        company = random.choice(TECH_GIANTS + STARTUPS + PRODUCT_COMPANIES)
    else:
        company = random.choice(ALL_COMPANIES)

    role = random.choice(ROLES_BY_CAREER[career])

    # Seniority adjustment based on years
    if years_since_grad >= 6 and "Senior" not in role and "Lead" not in role and \
       "Principal" not in role and "Director" not in role and "VP" not in role and \
       "Manager" not in role and "Founder" not in role and "CTO" not in role:
        if random.random() < 0.5:
            role = "Senior " + role

    return career, role, company, transitioned, prev_career


def generate_alumni(num_records=500):
    """Generate synthetic alumni records."""
    random.seed(42)
    records = []
    used_names = set()

    for i in range(num_records):
        # Name
        is_female = random.random() < 0.45
        first = random.choice(FIRST_NAMES_FEMALE if is_female else FIRST_NAMES_MALE)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"

        # Ensure unique names
        attempt = 0
        while full_name in used_names and attempt < 10:
            first = random.choice(FIRST_NAMES_FEMALE if is_female else FIRST_NAMES_MALE)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            attempt += 1
        if full_name in used_names:
            full_name = f"{first} {last} {random.choice('ABCDEFGHIJ')}"
        used_names.add(full_name)

        # Batch & Department
        batch_year = random.randint(2015, 2024)
        department = random.choice(DEPARTMENTS)

        # Career
        career, role, company, transitioned, prev_career = generate_career_path(department, batch_year)

        # Location
        if company in TECH_GIANTS and random.random() < 0.3:
            location = random.choice(GLOBAL_CITIES)
        else:
            location = random.choice(ALL_LOCATIONS)

        # Skills (3-7 from department pool + some cross-departmental)
        dept_skills = SKILLS_BY_DEPT.get(department, SKILLS_BY_DEPT["Computer Science"])
        num_skills = random.randint(3, 7)
        skills = random.sample(dept_skills, min(num_skills, len(dept_skills)))

        # Cross-pollinate skills for career transitioners
        if transitioned or career in ["data_science", "software_engineer"]:
            extra_skills = random.sample(
                SKILLS_BY_DEPT["Computer Science"],
                min(2, len(SKILLS_BY_DEPT["Computer Science"]))
            )
            skills = list(set(skills + extra_skills))[:7]

        skills_str = ", ".join(skills)

        # Bio
        bio = generate_bio(department, skills)

        # Transition note in bio
        if transitioned and prev_career:
            career_names = {
                "software_engineer": "software engineering",
                "data_science": "data science",
                "product": "product management",
                "research": "research",
                "management": "engineering management",
                "entrepreneur": "entrepreneurship",
                "consulting": "consulting",
                "domain_engineer": "core engineering",
            }
            prev_name = career_names.get(prev_career, prev_career)
            curr_name = career_names.get(career, career)
            bio += f" Transitioned from {prev_name} to {curr_name}."

        # Mentor (30% have mentors)
        mentor_id = ""
        if random.random() < 0.30:
            mentor_id = random.choice(MENTOR_NAMES)

        # Alumni ID
        alumni_id = str(i + 1001)

        records.append({
            "alumnus_id": alumni_id,
            "full_name": full_name,
            "batch_year": batch_year,
            "department": department,
            "current_company": company,
            "current_role": role,
            "city": location,
            "skills": skills_str,
            "bio": bio,
            "mentor_id": mentor_id,
            "phone": generate_phone(),
            "email": generate_email(full_name, company),
        })

    # Ensure Priya Ramesh exists for demo queries
    priya_idx = 0
    records[priya_idx] = {
        "alumnus_id": "1001",
        "full_name": "Priya Ramesh",
        "batch_year": 2020,
        "department": "Computer Science",
        "current_company": "Google",
        "current_role": "Senior SDE",
        "city": "Hyderabad",
        "skills": "Python, Machine Learning, TensorFlow, React, Deep Learning, Docker",
        "bio": "Passionate about building scalable AI systems. Led ML pipeline development at Google. Active open source contributor and tech community speaker. Previously interned at Microsoft Research.",
        "mentor_id": "Dr. Sharma",
        "phone": generate_phone(),
        "email": "priya.ramesh@google.com",
    }

    return records


def write_csv(records, output_path):
    """Write alumni records to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "alumnus_id", "full_name", "batch_year", "department",
        "current_company", "current_role", "city", "skills", "bio", "mentor_id",
        "phone", "email"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} alumni records -> {output_path}")


if __name__ == "__main__":
    records = generate_alumni(500)
    write_csv(records, ALUMNI_CSV_PATH)

    # Print sample
    print("\n--- Sample Records ---")
    for r in records[:3]:
        print(f"  {r['full_name']} | {r['batch_year']} | {r['department']} | {r['current_role']} @ {r['current_company']}")
    print(f"  ... and {len(records) - 3} more")
