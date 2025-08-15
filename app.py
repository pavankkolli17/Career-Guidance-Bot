import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# Utils (CSV readers/formatters)
# Expect these functions to exist in your utils:
# - utils.career_search: list_careers(), career_details(name_low)
# - utils.course_search: list_courses(), course_details(name_low)
from utils.career_search import list_careers, career_details
from utils.course_search import list_courses, course_details

app = Flask(__name__)

# ---------------- OpenAI (Clarify) ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def clarify_with_openai(question: str) -> str:
    """Return a WhatsApp-friendly, concise answer. Uses gpt-3.5-turbo."""
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

# ---------------- Health ----------------
@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

# ---------------- Web UI ----------------
@app.route("/", methods=["GET"])
def home():
    # Your templates/index.html shows three buttons (Browse Careers, Browse Courses, Clarify)
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_api():
    """
    Web JSON endpoint. Expects:
      { "user_id": "webuser-1", "message": "<text>" }
    Behaviours:
      - 'career' or 'careers' -> list careers (web shows clickable chips)
      - 'course' or 'courses' -> list courses
      - 'clarify: <question>' or any text ending with '?' -> OpenAI answer
      - otherwise: try exact => career or course details
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"response": "Choose: Browse Careers, Browse Courses, or Clarify."}), 400

    low = text.lower()

    # Clarify (stateless)
    if low.startswith("clarify:") or text.endswith("?"):
        q = text.split("clarify:", 1)[-1].strip() if low.startswith("clarify:") else text
        return jsonify({"response": clarify_with_openai(q)})

    # Explore Careers
    if low in ("career", "careers"):
        items, err = list_careers()
        if err or not items:
            return jsonify({"response": f"Error loading careers: {err or 'no data'}"}), 500
        return jsonify({
            "response": "Careers — click a name to view details, or press Clarify to ask a question.",
            "options": items
        })

    # Explore Courses
    if low in ("course", "courses"):
        items, err = list_courses()
        if err or not items:
            return jsonify({"response": f"Error loading courses: {err or 'no data'}"}), 500
        return jsonify({
            "response": "Courses — click a name to view details, or press Clarify to ask a question.",
            "options": items
        })

    # Try exact detail (career, then course)
    det, err = career_details(low)
    if not err and det and det != "Career not found.":
        return jsonify({"response": det})

    det2, err2 = course_details(low)
    if not err2 and det2 and det2 != "Course not found.":
        return jsonify({"response": det2})

    return jsonify({"response": "Not sure yet. Use the buttons above, or type 'clarify: <your question>'."})

# ---------------- Twilio WhatsApp ----------------
# Numbered-menu session store: phone => {mode: 'career'|'course'|None, options: [str]}
SESSION = {}

try:
    from twilio.twiml.messaging_response import MessagingResponse
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False

def _twilio_reply(text: str):
    """Return TwiML if twilio lib installed; else plain text."""
    if TWILIO_AVAILABLE:
        r = MessagingResponse()
        r.message(text)
        return str(r), 200, {"Content-Type": "application/xml"}
    return text, 200, {"Content-Type": "text/plain"}

@app.route("/twilio", methods=["POST"])
def twilio_webhook():
    """
    WhatsApp Sandbox/Business webhook:
      - 'career' -> numbered list of careers (reply 1/2/3…)
      - 'course' -> numbered list of courses (reply 1/2/3…)
      - 'clarify: <question>' or '?' -> OpenAI answer
      - numeric reply -> resolve against last list shown
      - exact text -> try details
    """
    from_number = (request.form.get("From") or "unknown").strip()
    body = (request.form.get("Body") or "").strip()
    low = body.lower()

    # If user replies with a number, map to the last shown options
    if low.isdigit() and from_number in SESSION and SESSION[from_number].get("options"):
        idx = int(low) - 1
        opts = SESSION[from_number]["options"]
        mode = SESSION[from_number].get("mode")
        if 0 <= idx < len(opts):
            selection = opts[idx].lower()
            if mode == "career":
                det, err = career_details(selection)
                SESSION[from_number] = {"mode": None, "options": []}
                return _twilio_reply(det if not err else f"Error: {err}")
            if mode == "course":
                det, err = course_details(selection)
                SESSION[from_number] = {"mode": None, "options": []}
                return _twilio_reply(det if not err else f"Error: {err}")
        return _twilio_reply("That number isn’t in the list. Reply 'career' or 'course' to see options again.")

    # Clarify (stateless)
    if low.startswith("clarify:") or body.endswith("?"):
        q = body.split("clarify:", 1)[-1].strip() if low.startswith("clarify:") else body
        return _twilio_reply(clarify_with_openai(q))

    # List careers (numbered)
    if low in ("career", "careers"):
        items, err = list_careers()
        if err or not items:
            return _twilio_reply(f"Error loading careers: {err or 'no data'}")
        SESSION[from_number] = {"mode": "career", "options": items}
        listing = "\n".join(f"{i+1}. {name}" for i, name in enumerate(items[:25]))
        return _twilio_reply(f"*Careers* — reply with a number:\n{listing}\n\nOr ask: clarify: <your question>")

    # List courses (numbered)
    if low in ("course", "courses"):
        items, err = list_courses()
        if err or not items:
            return _twilio_reply(f"Error loading courses: {err or 'no data'}")
        SESSION[from_number] = {"mode": "course", "options": items}
        listing = "\n".join(f"{i+1}. {name}" for i, name in enumerate(items[:25]))
        return _twilio_reply(f"*Courses* — reply with a number:\n{listing}\n\nOr ask: clarify: <your question>")

    # Fallback: try exact matches
    det, err = career_details(low)
    if not err and det and det != "Career not found.":
        SESSION[from_number] = {"mode": None, "options": []}
        return _twilio_reply(det)

    det2, err2 = course_details(low)
    if not err2 and det2 and det2 != "Course not found.":
        SESSION[from_number] = {"mode": None, "options": []}
        return _twilio_reply(det2)

    # Default help text
    return _twilio_reply(
        "Hi! Reply with 'career' to browse careers, 'course' to browse courses, "
        "or 'clarify: <question>' to ask anything. If you see a list, just reply with a number."
    )

# ---------------- Main ----------------
if __name__ == "__main__":
    # Render: Start Command = python app.py
    # Ensure OPENAI_API_KEY is set in Render → Environment
    app.run(host="0.0.0.0", port=5000, debug=True)