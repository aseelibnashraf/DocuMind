import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from rag import ask, build_index

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024   # 10 MB upload limit

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return "DocuMind is running"

@app.route("/about")
def about():
    return "Built by Aseel"

@app.route("/contact")
def contact():
    return "aseelibnashraf@gmail.com"

@app.route("/ask", methods=["GET", "POST"])
def ask_page():
    question, answer, sources = "", "", []
    if request.method == "POST":
        question = request.form["question"]
        answer, sources = ask(question)
    return render_template("ask.html", question=question, answer=answer, sources=sources)

@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    message = ""
    if request.method == "POST":
        f = request.files["pdf"]
        if not f.filename.lower().endswith(".pdf"):
            message = "Please upload a PDF file."
        else:
            path = os.path.join(UPLOAD_DIR, secure_filename(f.filename))
            f.save(path)
            build_index(path)
            message = f"Uploaded {f.filename}. You can now ask questions about it."
    return render_template("upload.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)