# ============================================================
# FILE: ai_server/server.py
# CeylonMate — Python AI Microservice (runs on port 5001)
# This is a SEPARATE small server just for artifact detection
# Your Node.js backend on port 5000 stays UNTOUCHED
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)  # Allow requests from React Native and Node.js

# ── Load YOLOv8 model once when server starts ────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best_model.pt')
model = None

def get_model():
    global model
    if model is None:
        print(f"🤖 Loading YOLOv8 model...")
        model = YOLO(MODEL_PATH)
        print(f"✅ Model loaded! Classes: {list(model.names.values())}")
    return model

# ── Artifact info database ───────────────────────────────────
ARTIFACT_INFO = {
    'Buddha_Statue': {
        'name': 'Buddha Statue',
        'sinhala': 'බුදු පිළිමය',
        'period': '3rd Century BCE – 12th Century CE',
        'sites': ['Anuradhapura', 'Polonnaruwa', 'Dambulla'],
        'description': 'Buddhist statues in Sri Lanka represent Gautama Buddha in various poses (mudras). The most iconic are the massive standing and seated statues at Aukana and Polonnaruwa, carved directly from rock. They reflect the artistic mastery of ancient Sinhala craftsmen.',
        'significance': 'Placed at temples as objects of veneration. Pilgrims circumambulate them while chanting pirith (sacred verses).',
        'material': 'Granite, Limestone, Brick (gilded)',
        'height': 'Ranges from 0.3m to 15m+',
        'icon': '🧘',
        'color': '#B45309',
        'lightColor': '#FEF3C7',
    },
    'Moonstone': {
        'name': 'Moonstone',
        'sinhala': 'සඳකඩ පහන',
        'period': '4th – 12th Century CE',
        'sites': ['Anuradhapura', 'Polonnaruwa', 'Medirigiriya'],
        'description': 'The Moonstone (Sandakada Pahana) is a semi-circular carved stone placed at temple staircases, featuring concentric bands of elephants, horses, lions, bulls, geese, and lotus petals.',
        'significance': 'Each band carries deep symbolic meaning. The lotus at center represents nirvana — the goal of Buddhist practice.',
        'material': 'Granite, Limestone',
        'height': '0.3m – 0.6m thick, 1m – 2m diameter',
        'icon': '🌙',
        'color': '#1D4ED8',
        'lightColor': '#DBEAFE',
    },
    'Guardstone': {
        'name': 'Guardstone',
        'sinhala': 'මුරගල',
        'period': '4th – 8th Century CE',
        'sites': ['Anuradhapura', 'Polonnaruwa'],
        'description': 'Guardstones are upright stone slabs placed on either side of stairways to sacred buildings, depicting a deity standing on a mythical sea creature (makara).',
        'significance': 'Believed to protect the sacred building from evil spirits and malevolent forces.',
        'material': 'Limestone, Granite',
        'height': '1m – 1.5m',
        'icon': '🗿',
        'color': '#065F46',
        'lightColor': '#D1FAE5',
    },
    'Stone_Pillar': {
        'name': 'Stone Pillar',
        'sinhala': 'ගල් කුළුණ',
        'period': '3rd Century BCE – 12th Century CE',
        'sites': ['Anuradhapura', 'Polonnaruwa', 'Sigiriya'],
        'description': 'Ancient stone pillars served structural, ceremonial, and inscriptional purposes. The 1,600 stone columns at the Brazen Palace are remarkable ancient engineering feats in South Asia.',
        'significance': 'Used as structural columns, ceremonial lamp posts, and surfaces for royal inscriptions.',
        'material': 'Granite',
        'height': '2m – 8m',
        'icon': '🏛️',
        'color': '#6B21A8',
        'lightColor': '#F3E8FF',
    },
    'Mural': {
        'name': 'Mural Painting',
        'sinhala': 'බිතු සිතුවම',
        'period': '1st Century BCE – 18th Century CE',
        'sites': ['Dambulla', 'Sigiriya', 'Degaldoruwa'],
        'description': 'Sri Lankan murals are among the finest in Asian painting. The Sigiriya frescoes (5th century) are among the oldest surviving paintings in the world.',
        'significance': 'Murals depicted Jataka tales and royal ceremonies to educate Buddhist devotees.',
        'material': 'Natural pigments on lime plaster',
        'height': 'Wall-sized panels',
        'icon': '🎨',
        'color': '#B91C1C',
        'lightColor': '#FEE2E2',
    },
    'Inscription_Slab': {
        'name': 'Inscription Slab',
        'sinhala': 'ශිලා ලේඛනය',
        'period': '3rd Century BCE – 12th Century CE',
        'sites': ['Anuradhapura', 'Polonnaruwa', 'Mihintale'],
        'description': 'Stone tablets bearing royal edicts, land grants, and religious proclamations in ancient Sinhala, Pali, Tamil, and Sanskrit scripts.',
        'significance': 'Primary historical records of ancient Sri Lankan governance, religion, and social structure.',
        'material': 'Limestone, Granite',
        'height': '0.5m – 3m',
        'icon': '📜',
        'color': '#92400E',
        'lightColor': '#FEF3C7',
    },
    'Stupa_Model': {
        'name': 'Stupa Model',
        'sinhala': 'දාගැබ් ආකෘතිය',
        'period': '3rd Century BCE – Present',
        'sites': ['Anuradhapura', 'Polonnaruwa', 'Kandy'],
        'description': 'Miniature stupa models created as votive offerings, replicating the hemispherical dome that enshrines Buddhist relics.',
        'significance': 'The stupa symbolizes the mind of the Buddha. The dome represents the cosmic mountain, the spire points to nirvana.',
        'material': 'Stone, Clay, Bronze',
        'height': '0.1m – 1m (models)',
        'icon': '⛩️',
        'color': '#0F766E',
        'lightColor': '#CCFBF1',
    },
}

# ── ROUTE: Health check ──────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    try:
        m = get_model()
        return jsonify({
            'status': 'ready',
            'model': 'YOLOv8n CeylonMate',
            'classes': list(m.names.values()),
            'port': 5001
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ── ROUTE: Detect artifact ───────────────────────────────────
@app.route('/detect', methods=['POST'])
def detect():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        file = request.files['image']
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        yolo = get_model()
        results = yolo.predict(
            source=image,
            conf=0.25,
            iou=0.6,
            imgsz=640,
            verbose=False,
        )

        detections = []
        for result in results:
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = yolo.names[class_id]
                    detections.append({
                        'class_name': class_name,
                        'confidence': round(confidence, 4),
                        'info': ARTIFACT_INFO.get(class_name, {}),
                    })

        if not detections:
            return jsonify({
                'detected': False,
                'message': 'No artifact detected. Try better lighting or a closer angle.',
            })

        detections.sort(key=lambda x: x['confidence'], reverse=True)
        best = detections[0]

        return jsonify({
            'detected': True,
            'class_name': best['class_name'],
            'confidence': best['confidence'],
            'info': best['info'],
            'total_found': len(detections),
        })

    except Exception as e:
        print(f"Detection error: {e}")
        return jsonify({'error': 'Detection failed. Please try again.'}), 500

# ── Start server ─────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("🏛️  CeylonMate AI Server")
    print("=" * 50)
    print("Loading model on startup...")
    get_model()  # Pre-load model so first request is fast
    print("\n✅ Server starting on http://localhost:5001")
    print("   Health check: http://localhost:5001/health")
    print("   Detection:    POST http://localhost:5001/detect")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)
