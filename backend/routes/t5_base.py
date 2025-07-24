import os

from flask import Flask, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
import torch
from dotenv import load_dotenv

# === Initialisation Flask ===
app = Flask(__name__)



csrf = CSRFProtect(app)
t5_base_bp = Blueprint('t5', __name__)

# === Chargement du modèle T5 fine-tuné ===
MODEL_PATH = "TahalliAnas/t5_base_ConfigFiles_fixer"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
t5_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

# === Configuration Gemini API ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

@t5_base_bp.route("/t5", methods=["POST"])
@jwt_required()
def correct_dockerfile():
    data = request.get_json()
    dockerfile = data.get("dockerfile", "")

    if not dockerfile.strip():
        return jsonify({"error": "Le champ 'dockerfile' est requis"}), 400

    # --- Étape 1 : Génération du Dockerfile corrigé avec T5 ---
    prompt = (
        "Fix security issues in this Dockerfile:\n"
        f"{dockerfile}"
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(t5_model.device)
    with torch.no_grad():
        outputs = t5_model.generate(**inputs, max_length=512)
        correction = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Nettoyage brut
    fixed_code = correction.strip()
    fixed_code = fixed_code.replace("\\n", "\n").replace("\\\\", "\\")

    # Ajout de retour à la ligne entre les instructions Docker
    docker_instructions = [
        "FROM", "RUN", "CMD", "COPY", "ADD", "WORKDIR", "USER",
        "EXPOSE", "ENV", "ENTRYPOINT", "VOLUME", "LABEL", "ARG", "HEALTHCHECK"
    ]
    for instr in docker_instructions:
        fixed_code = fixed_code.replace(f" {instr} ", f"\n{instr} ")
        fixed_code = fixed_code.replace(f"{instr} ", f"\n{instr} ")

    fixed_code = fixed_code.strip()

    # --- Étape 2 : Génération de l'explication avec Gemini ---
    explanation_prompt = f"""
    here is the docker file before and after  :

    🔧 Before :
    {dockerfile}

    ✅ After :
    {fixed_code}

        Can you explain the changes line by line to show how the corrected version improves security or best practices?    """

    try:
        gemini_response = gemini_model.generate_content(explanation_prompt)
        explanation = gemini_response.text.strip()
    except Exception as e:
        explanation = f"[Erreur Gemini] Impossible to generate explications: {e}"

    # --- Réponse finale ---
    return jsonify({
        "correction": fixed_code,
        "explanation": explanation
    }), 200
