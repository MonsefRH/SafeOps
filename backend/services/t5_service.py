import os
import logging
import torch
from datetime import datetime ,UTC
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
from utils.db import db
from models.scan_history import ScanHistory
from models.user import User
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from services.email_template import EMAIL_ADDRESS, EMAIL_PASSWORD

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('t5_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

MODEL_PATH = "TahalliAnas/t5_base_ConfigFiles_fixer"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
t5_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

def _send_finish_email_t5(to_email: str, user_name: str, executed_at: str):
    """Send a beautiful HTML email when T5 Dockerfile generation is done."""
    subject = f" SafeOps — T5: Dockerfile Generation Completed"
    html_body = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            margin: 0;
            padding: 0;
          }}
          .container {{
            max-width: 650px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            overflow: hidden;
          }}
          .header {{
            background: #1565c0;
            color: #fff;
            padding: 20px 30px;
            font-size: 22px;
            font-weight: 600;
          }}
          .content {{
            padding: 30px;
            line-height: 1.6;
          }}
          .footer {{
            background: #f0f3f7;
            color: #666;
            font-size: 13px;
            text-align: center;
            padding: 15px;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">SafeOps T5 Dockerfile Generator</div>
          <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>The Dockerfile generation and correction process has been successfully completed.</p>
            <ul>
                <li><strong>Executed at:</strong> {executed_at}</li>
                <li><strong>Status:</strong> <span style="color:#16a34a;font-weight:600;">Completed</span></li>
            </ul>

            <p>You can now view the updated Dockerfile directly from your SafeOps dashboard.</p>
            <p>Thank you for using <strong>SafeOps</strong>!</p>
          </div>
          <div class="footer">
            &copy; {datetime.now(UTC).year} SafeOps — Automated Security Platform
          </div>
        </div>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content("Please enable HTML view to see this message.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def correct_dockerfile(user_id, dockerfile):
    """Corrige un Dockerfile via T5 + explication Gemini. Envoie un email simple (pas de CSV)."""
    if not dockerfile.strip():
        logger.error("Empty Dockerfile provided")
        raise ValueError("Le champ 'dockerfile' est requis")

    try:
        # T5 correction
        prompt = "Fix security issues in this Dockerfile:\n" + dockerfile
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(t5_model.device)
        with torch.no_grad():
            outputs = t5_model.generate(**inputs, max_length=512)
        correction = tokenizer.decode(outputs[0], skip_special_tokens=True)

        fixed_code = correction.strip().replace("\\n", "\n").replace("\\\\", "\\")
        for instr in ["FROM", "RUN", "CMD", "COPY", "ADD", "WORKDIR", "USER",
                      "EXPOSE", "ENV", "ENTRYPOINT", "VOLUME", "LABEL", "ARG", "HEALTHCHECK"]:
            fixed_code = fixed_code.replace(f" {instr} ", f"\n{instr} ")
            fixed_code = fixed_code.replace(f"{instr} ", f"\n{instr} ")
        fixed_code = fixed_code.strip()

        # Gemini explanation
        explanation_prompt = f"""
Here is the Dockerfile before and after:

🔧 Before:
{dockerfile}

 After:
{fixed_code}

Explain line by line how the corrected version improves security/best practices.
"""
        try:
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            gemini_response = gemini_model.generate_content(explanation_prompt)
            explanation = (gemini_response.text or "").strip()
        except Exception as e:
            logger.warning(f"Gemini error: {str(e)}")
            explanation = f"[Erreur Gemini] Impossible de générer les explications: {str(e)}"

        # Save in DB
        executed_at = datetime.now(UTC).isoformat() + "Z"
        result = {
            "status": "success",
            "correction": fixed_code,
            "explanation": explanation,
            "meta": {"executed_at": executed_at}
        }
        scan = ScanHistory(
            user_id=user_id,
            scan_result=result,
            status="success",
            score=100,
            compliant=True,
            input_type="content",
            scan_type="t5"
        )
        db.session.add(scan)
        db.session.commit()
        logger.info(f"Saved T5 scan with ID {scan.id} for user_id {user_id}")

        # Email simple (pas de CSV)
        try:
            user = db.session.get(User, int(user_id))
            if user:
                _send_finish_email_t5(user.email, user.name, executed_at)
        except Exception as e:
            logger.warning(f"T5 finish email failed for scan_id {scan.id}: {e}")

        return {"scan_id": scan.id, "correction": fixed_code, "explanation": explanation}

    except Exception as e:
        logger.error(f"Failed to process Dockerfile for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"Failed to process Dockerfile: {str(e)}")
