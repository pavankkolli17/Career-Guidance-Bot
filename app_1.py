import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

from utils.career_search import list_careers, career_details
from utils.course_search import list_courses, course_details

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)

def clarify_with_openai(question: str) -> str:
    if not client:
        return ("Clarify is enabled, but OPENAI_API_KEY is missing. "
                "Set it in your environment and redeploy.")
    system_msg = (
        "You are a concise, student-friendly guidance assistant for Indian students. "
        "Reply in WhatsApp-friendly bullet points when useful. "
        "Keep answers crisp and practical. If unsure, say so briefly."
    )
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question.strip()}
        ],
        temperature=0.4,
        max_tokens=400
    )
    return resp.choices[0].message.content.strip()

@app.route("/health")
def health():
    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_api():
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"response": "Choose an option: Browse Careers, Browse Courses, or Clarify."}), 400

    low = text.lower()

    if low.startswith("clarify:") or text.endswith("?"):
        q = text.split("clarify:", 1)[-1].strip() if low.startswith("clarify:") else text
        return jsonify({"response": clarify_with_openai(q)})

    if low in ("career", "careers"):
        items, err = list_careers()
        if err:
            return jsonify({"response": f"Error loading careers: {err}"}), 500
        return jsonify({
            "response": "Careers — click a name to view details, or press Clarify to ask a question.",
            "options": items
        })

    if low in ("course", "courses"):
        items, err = list_courses()
        if err:
            return jsonify({"response": f"Error loading courses: {err}"}), 500
        return jsonify({
            "response": "Courses — click a name to view details, or press Clarify to ask a question.",
            "options": items
        })

    det, err = career_details(low)
    if not err and det and det != "Career not found.":
        return jsonify({"response": det})

    det2, err2 = course_details(low)
    if not err2 and det2 and det2 != "Course not found.":
        return jsonify({"response": det2})

    return jsonify({"response": "Not sure yet. Use the buttons above, or type 'clarify: <your question>'."})

try:
    from twilio.twiml.messaging_response import MessagingResponse
    TWILIO = True
except Exception:
    TWILIO = False

@app.route("/twilio", methods=["POST"])
def twilio_webhook():
    body = (request.form.get("Body") or "").strip()
    low = body.lower()

    def reply(txt):
        if TWILIO:
            r = MessagingResponse()
            r.message(txt)
            return str(r), 200, {"Content-Type": "application/xml"}
        return txt, 200, {"Content-Type": "text/plain"}

    if low.startswith("clarify:") or body.endswith("?"):
        q = body.split("clarify:", 1)[-1].strip() if low.startswith("clarify:") else body
        return reply(clarify_with_openai(q))

    if low in ("career", "careers"):
        items, err = list_careers()
        if err: return reply(f"Error loading careers: {err}")
        head = "Careers (reply with the exact name):"
        listing = "\n".join(f"- {c}" for c in items[:30])
        return reply(f"{head}\n{listing}\n\nOr ask: clarify: <your question>")

    if low in ("course", "courses"):
        items, err = list_courses()
        if err: return reply(f"Error loading courses: {err}")
        head = "Courses (reply with the exact name):"
        listing = "\n".join(f"- {c}" for c in items[:30])
        return reply(f"{head}\n{listing}\n\nOr ask: clarify: <your question>")

    det, err = career_details(low)
    if not err and det and det != "Career not found.":
        return reply(det)
    det2, err2 = course_details(low)
    if not err2 and det2 and det2 != "Course not found.":
        return reply(det2)

    return reply("Hi! Reply with 'career' to browse careers, 'course' to browse courses, or 'clarify: <question>' to ask anything.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
