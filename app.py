from flask import Flask, render_template, request, send_file, send_from_directory
from agent.orchestrator import generate_threat_model

import os

app = Flask(__name__)

# Allow diagrams.net viewer to use eval/new Function (local demo only!)
@app.after_request
def add_csp(response):
    csp = (
        "default-src 'self' https://viewer.diagrams.net; "
        "script-src 'self' 'unsafe-eval' https://viewer.diagrams.net; "
        "style-src 'self' 'unsafe-inline' https://viewer.diagrams.net; "
        "img-src 'self' data: https://viewer.diagrams.net; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'self';"
    )
    response.headers["Content-Security-Policy"] = csp
    return response

# Home page to input form
@app.route('/')
def index():
    return render_template('index.html')

# Process the system description → produce threats + diagram
@app.route('/generate', methods=['POST'])
def generate():
    description = request.form.get('description')

    results = generate_threat_model(description)

    # results = {
    #   "components": [...],
    #   "actors": [...],
    #   "flows": [...],
    #   "threats": [...],
    #   "diagram_path": "outputs/diagram.drawio"
    # }

    diagram_xml = ""
    try:
        with open(results["diagram_path"], "r", encoding="utf-8") as f:
            diagram_xml = f.read()
    except FileNotFoundError:
        diagram_xml = ""

    stripped = diagram_xml.lstrip()
    if stripped.startswith("<mxGraphModel"):
        diagram_xml = f"<mxfile><diagram>{diagram_xml}</diagram></mxfile>"

    # Build config dict for viewer
    mx_config = {
        "highlight": "#0000ff",
        "nav": True,
        "resize": True,
        "dark-mode": "auto",
        "toolbar": "zoom layers tags lightbox",
        "edit": "_blank",
        "xml": diagram_xml,
    }

    return render_template(
        'results.html',
        threats=results["threats"],
        components=results["components"],
        actors=results["actors"],
        flows=results["flows"],
        diagram_path=results["diagram_path"],
        diagram_xml=diagram_xml,
        mx_config=mx_config,
    )

# Download the generated diagram
@app.route('/download')
def download():
    return send_file('outputs/diagram.drawio', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
