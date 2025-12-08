import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads .env
client = OpenAI(api_key=os.getenv("API_KEY"))

from .diagram_generator import generate_drawio_diagram


def _extract_json_from_text(text):
    """
    Try to pull JSON out of an LLM response.
    Handles ```json fences and extra text.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip("` \n")

    # Direct attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: first {...} or [...] block
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        snippet = match.group(1)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None

    return None


def llm_parse_system(description: str):
    prompt = f"""
You are a cybersecurity threat modeling assistant.

Read the following system description and extract:

- actors (end-users, admins, external services)
- components (backend services, databases, frontends, APIs, queues, etc.)
- data flows between actors and components or between components.

Return ONLY valid JSON in this exact format:

{{
  "actors": ["Actor1", "Actor2"],
  "components": ["Component1", "Component2"],
  "flows": ["Actor1 -> Component1: short description", "Component1 -> Component2: short description"]
}}
    
System description:
\"\"\"{description}\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content

    # Try to parse JSON response
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Very defensive fallback so your app doesn't crash
        data = {
            "actors": ["User"],
            "components": ["Core Application"],
            "flows": [],
        }

    # Normalize types
    actors = data.get("actors") or ["User"]
    components = data.get("components") or ["Core Application"]
    flows = data.get("flows") or []

    return actors, components, flows



def llm_generate_threats(description: str, components):
    prompt = f"""
You are a STRIDE-based threat modeling expert.

The system is described as:
\"\"\"{description}\"\"\"

The identified components are:
{components}

For each relevant STRIDE category (Spoofing, Tampering, Repudiation,
Information Disclosure, Denial of Service, Elevation of Privilege),
generate realistic threats tied to these components.

Return ONLY valid JSON as a list of objects like:

[
  {{
    "title": "Short threat title",
    "category": "Spoofing",
    "component": "Component name",
    "description": "1-3 sentence explanation of the threat."
  }}
]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    raw = response.choices[0].message.content

    data = _extract_json_from_text(raw)

    if not data:
        # Fallback so you never show an empty panel
        return _generate_stride_threats(components)

    cleaned = []
    for t in data:
        cleaned.append({
            "title": t.get("title", "Threat"),
            "category": t.get("category", "Unknown"),
            "component": t.get("component", "Unknown component"),
            "description": t.get("description", ""),
        })

    if not cleaned:
        # Also fallback if model returned []
        return _generate_stride_threats(components)

    return cleaned



# TESTER (CHANGE LATER FOR AGENTIC AI)
def _extract_actors(description: str):
    description_lower = description.lower()
    actors = set()

    if "user" in description_lower:
        actors.add("User")
    if "customer" in description_lower:
        actors.add("Customer")
    if "admin" in description_lower or "administrator" in description_lower:
        actors.add("Admin")

    # default if nothing detected
    if not actors:
        actors.add("External Actor")

    return list(actors)


# TESTER (CHANGE LATER FOR AGENTIC AI)
def _extract_components(description: str):
    description_lower = description.lower()
    components = set()

    # Very naive keyword-based detection
    if "flask" in description_lower or "api" in description_lower:
        components.add("Flask API Server")
    if "react" in description_lower or "frontend" in description_lower:
        components.add("Frontend Web App")
    if "database" in description_lower or "db" in description_lower:
        components.add("Database")
    if "mongo" in description_lower or "mongodb" in description_lower:
        components.add("MongoDB")
    if "postgres" in description_lower or "postgresql" in description_lower:
        components.add("PostgreSQL")
    if "payment" in description_lower:
        components.add("Payment Service")
    if "auth" in description_lower or "login" in description_lower:
        components.add("Authentication Service")
    if "admin panel" in description_lower or "admin dashboard" in description_lower:
        components.add("Admin Dashboard")

    # Fallback if nothing recognized
    if not components:
        components.add("Core Application")

    # Make sure list is stable
    return list(components)



def _infer_flows(actors, components):
    flows = []

    if actors and components:
        first_component = components[0]
        for actor in actors:
            flows.append(f"{actor} → {first_component}: sends requests")

    # Connect components sequentially
    for i in range(len(components) - 1):
        src = components[i]
        dst = components[i + 1]
        flows.append(f"{src} → {dst}: forwards data")

    return flows

# TESTER (CHANGE FOR AGENTIC AI)
def _generate_stride_threats(components):
    threats = []

    for comp in components:
        # Spoofing
        threats.append({
            "title": "Spoofed identity",
            "category": "Spoofing",
            "component": comp,
            "description": f"An attacker may impersonate a legitimate user or service when interacting with {comp}."
        })

        # Tampering
        threats.append({
            "title": "Data tampering",
            "category": "Tampering",
            "component": comp,
            "description": f"Unvalidated or unprotected inputs to {comp} could allow modification of critical data."
        })

        # Information Disclosure
        threats.append({
            "title": "Sensitive data exposure",
            "category": "Information Disclosure",
            "component": comp,
            "description": f"{comp} might expose sensitive data if encryption, access control, or logging is misconfigured."
        })

        # Denial of Service
        threats.append({
            "title": "Denial of Service",
            "category": "Denial of Service",
            "component": comp,
            "description": f"{comp} could be overwhelmed by high traffic or expensive operations, making the system unavailable."
        })

    return threats


def generate_threat_model(description: str):
    """
    Agentic pipeline:
      1. Use ChatGPT to parse the system into actors, components, and flows.
      2. Use ChatGPT again to generate STRIDE threats.
      3. Use our diagram tool to generate a draw.io diagram.
    """

    # 1) LLM parses the system description
    actors, components, flows = llm_parse_system(description)

    # 2) LLM generates STRIDE threats
    threats = llm_generate_threats(description, components)

    # 3) Generate diagram based on actors + components (+ optional flows)
    os.makedirs("outputs", exist_ok=True)
    diagram_path = generate_drawio_diagram(
        actors,
        components,
        flows,
        output_path="outputs/diagram.drawio"
    )

    return {
        "components": components,
        "actors": actors,
        "flows": flows,
        "threats": threats,
        "diagram_path": diagram_path,
    }
