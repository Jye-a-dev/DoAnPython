from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Flashcard

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/cards", methods=["GET"])
def get_cards():
    cards = Flashcard.query.all()
    return jsonify([card.to_dict() for card in cards])

@api_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    text = data.get("text", "")
    
    # Mock xử lý sinh flashcard từ input text
    new_card = Flashcard(question="Khái niệm từ bài học", answer=text[:50] + "...")
    db.session.add(new_card)
    db.session.commit()
    
    return jsonify({"cards": [new_card.to_dict()]}), 201
