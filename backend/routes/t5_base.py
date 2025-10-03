import os
import logging

from flask import Flask, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
from flask_wtf.csrf import CSRFProtect
import torch
from pydantic import ValidationError
from dotenv import load_dotenv

from schemas.t5_dto import T5Request, T5Response, T5ErrorResponse
from services.t5_service import correct_dockerfile

# Configure logging
logger = logging.getLogger(__name__)

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
def correct_dockerfile_route():
    try:
        data = T5Request(**request.get_json())
        user_id = get_jwt_identity()
        result = correct_dockerfile(user_id, data.dockerfile)
        return jsonify(T5Response(**result).dict()), 200
    except ValidationError as e:
        logger.error(f"Invalid input for T5 correction: {str(e)}")
        return jsonify(T5ErrorResponse(error="Invalid input", details=str(e)).dict()), 400
    except ValueError as e:
        logger.error(f"T5 correction error: {str(e)}")
        return jsonify(T5ErrorResponse(error=str(e)).dict()), 400
    except RuntimeError as e:
        logger.error(f"Server error during T5 correction: {str(e)}")
        return jsonify(T5ErrorResponse(error=str(e)).dict()), 500