import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
from utils.db import db
from models.scan_history import ScanHistory
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
    handlers=[logging.FileHandler('t5_app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

# Load T5 model
MODEL_PATH = "TahalliAnas/t5_base_ConfigFiles_fixer"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
t5_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

def correct_dockerfile(user_id, dockerfile):
    """Correct a Dockerfile using T5 and generate explanations with Gemini."""
    if not dockerfile.strip():
        logger.error("Empty Dockerfile provided")
        raise ValueError("Le champ 'dockerfile' est requis")

    try:
        # Step 1: Generate corrected Dockerfile with T5
        prompt = (
            "Fix security issues in this Dockerfile:\n"
            f"{dockerfile}"
        )
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(t5_model.device)
        with torch.no_grad():
            outputs = t5_model.generate(**inputs, max_length=512)
        correction = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Clean up the output
        fixed_code = correction.strip()
        fixed_code = fixed_code.replace("\\n", "\n").replace("\\\\", "\\")

        # Add newlines between Docker instructions
        docker_instructions = [
            "FROM", "RUN", "CMD", "COPY", "ADD", "WORKDIR", "USER",
            "EXPOSE", "ENV", "ENTRYPOINT", "VOLUME", "LABEL", "ARG", "HEALTHCHECK"
        ]
        for instr in docker_instructions:
            fixed_code = fixed_code.replace(f" {instr} ", f"\n{instr} ")
            fixed_code = fixed_code.replace(f"{instr} ", f"\n{instr} ")
        fixed_code = fixed_code.strip()

        # Step 2: Generate explanation with Gemini
        explanation_prompt = f"""
        Here is the Dockerfile before and after:

        🔧 Before:
        {dockerfile}

        ✅ After:
        {fixed_code}

        Can you explain the changes line by line to show how the corrected version improves security or best practices?
        """
        try:
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            gemini_response = gemini_model.generate_content(explanation_prompt)
            explanation = gemini_response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini error: {str(e)}")
            explanation = f"[Erreur Gemini] Impossible de générer les explications: {str(e)}"

        # Step 3: Save to database
        result = {
            "status": "success",
            "correction": fixed_code,
            "explanation": explanation
        }
        scan = ScanHistory(
            user_id=user_id,
            scan_result=result,
            status="success",
            score=100,  # No compliance check, assume success
            compliant=True,
            input_type="content",
            scan_type="t5"
        )
        db.session.add(scan)
        db.session.commit()
        logger.info(f"Saved T5 scan with ID {scan.id} for user_id {user_id}")

        return {
            "scan_id": scan.id,
            "correction": fixed_code,
            "explanation": explanation
        }

    except Exception as e:
        logger.error(f"Failed to process Dockerfile for user_id {user_id}: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"Failed to process Dockerfile: {str(e)}")