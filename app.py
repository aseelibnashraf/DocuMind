import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from rag import ask, build_index
from html import escape

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
    answer_html = ""
    if request.method == "POST":
        question = request.form["question"]
        answer, pages = ask(question)
        answer_html = f"<p><b>Q:</b> {escape(question)}</p><p>{escape(answer)}</p><p><i>Sources: {", ".join(pages)}</i></p>"
    return f"""
    <h1>DocuMind</h1>
    <form method="post">
        <input name="question" placeholder="Ask about the handbook" size="50" required>
        <button>Ask</button>
    </form>
    {answer_html}
    """
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
            message = f"Uploaded {escape(f.filename)}. You can now ask questions about it."
    return f"""
    <h1>Upload a PDF</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="pdf" accept=".pdf" required>
        <button>Upload</button>
    </form>
    <p>{message}</p>
    <p><a href="/ask">Go to Ask</a></p>
    """
if __name__ == "__main__":
    app.run(debug=True)