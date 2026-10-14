from flask import Flask, request
from rag import ask
from html import escape

app = Flask(__name__)

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
        answer_html = f"<p><b>Q:</b> {escape(question)}</p><p>{escape(answer)}</p><p><i>Pages: {pages}</i></p>"
    return f"""
    <h1>DocuMind</h1>
    <form method="post">
        <input name="question" placeholder="Ask about the handbook" size="50" required>
        <button>Ask</button>
    </form>
    {answer_html}
    """

if __name__ == "__main__":
    app.run(debug=True)