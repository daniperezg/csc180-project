from flask import Flask, render_template, request, send_file
from agent.orchestrator import generate_threat_model

app = Flask(__name__)

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

    return render_template(
        'results.html',
        threats=results["threats"],
        components=results["components"],
        actors=results["actors"],
        flows=results["flows"],
        diagram_path=results["diagram_path"]
    )

# Download the generated diagram
@app.route('/download')
def download():
    return send_file('outputs/diagram.drawio', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
