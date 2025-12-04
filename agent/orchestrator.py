import os
from .diagram_generator import generate_drawio_diagram

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
    Main entry point for the agent.

    - Extracts actors, components, flows from description
    - Generates a simple STRIDE-based threat list
    - Produces a draw.io diagram and returns its path + structured data
    """

    # 1. Extract structure
    actors = _extract_actors(description)
    components = _extract_components(description)
    flows = _infer_flows(actors, components)

    # 2. Generate STRIDE threats
    threats = _generate_stride_threats(components)

    # 3. Generate diagram
    os.makedirs("outputs", exist_ok=True)
    diagram_path = generate_drawio_diagram(actors, components, flows, output_path="outputs/diagram.drawio")

    # 4. Return everything for the Flask template
    return {
        "components": components,
        "actors": actors,
        "flows": flows,
        "threats": threats,
        "diagram_path": diagram_path,
    }
