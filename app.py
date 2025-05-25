from flask import Flask, render_template, request, session, redirect, url_for
import os
import requests

app = Flask(__name__)
app.secret_key = os.urandom(16)

AWAN_API_KEY = "3b38e8c8-5a6b-4e7e-a373-f85048d14675"  # Replace with your actual Awan API key
AWAN_API_URL = "https://api.awanllm.com/v1/completions"


def build_prompt(question, edu_type, subject, marks, class_level, semester, conversation_history=None):
    level_detail = f"Class {class_level}" if edu_type == "School" else f"Semester {semester}"
    marks_value = marks.split()[0] if marks else "5"

    prompt = (
        "You are an experienced teacher and exam preparation expert. "
        "Provide a clear, concise, and exam-oriented answer and include relevant source links at the end.\n\n"
    )

    if conversation_history:
        prompt += "Conversation history:\n"
        for line in conversation_history:
            prompt += line + "\n"
        prompt += "\n"

    prompt += (
        f"A student from {level_detail} studying {subject} has asked:\n"
        f"Question: {question}\n\n"
        f"Please provide an answer suitable for a {marks_value}-mark question. "
        "Ensure the answer is clear, well-structured, and includes a separate section for source links.\n"
        "Answer:"
    )

    return prompt


def query_awan_api(prompt):
    headers = {
        "Authorization": f"Bearer {AWAN_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Meta-Llama-3-70B-Instruct",
        "prompt": prompt,
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9
    }
    response = requests.post(AWAN_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("result", "No result found.")
    else:
        return f"Error: {response.status_code} - {response.text}"


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    answer = None

    if "conversation" not in session:
        session["conversation"] = []

    if request.method == "POST":
        question = request.form.get("question")
        edu_type = request.form.get("edu_type")
        subject = request.form.get("subject")
        marks = request.form.get("marks")
        class_level = request.form.get("class_level")
        semester = request.form.get("semester")

        if not question or not edu_type or not subject or not marks:
            error = "Please fill all required fields."
        else:
            prompt = build_prompt(
                question,
                edu_type,
                subject,
                marks,
                class_level,
                semester,
                session["conversation"]
            )
            answer = query_awan_api(prompt)

            # Store Q&A in conversation history
            session["conversation"].append(f"Q: {question}")
            session["conversation"].append(f"A: {answer}")
            session.modified = True

    return render_template("index.html", error=error, answer=answer, conversation=session.get("conversation"))


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
