import tensorflow as tf
import cv2
import numpy as np
import os
import json
import sys

# ===============================
# 1. LOAD MODEL
# ===============================
# Use a path relative to this script so it works regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'web_app', 'skin_disease_model.h5')
if not os.path.exists(model_path):
    # fallback to root location if needed
    model_path = os.path.join(BASE_DIR, 'skin_disease_model.h5')

model = tf.keras.models.load_model(model_path)

# ===============================
# 2. GET IMAGE PATH FROM USER INPUT OR STDIN
# ===============================
img_path = None
temp_file = None

if len(sys.argv) >= 2:
    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(json.dumps({"error": f"Image file not found: {img_path}"}))
        sys.exit(1)
    image_name = os.path.basename(img_path)
else:
    # Try to read raw image bytes from stdin (allows piping/uploaded bytes)
    try:
        data = sys.stdin.buffer.read()
    except Exception:
        data = b''

    if data:
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        with open(temp_path, 'wb') as f:
            f.write(data)
        img_path = temp_path
        temp_file = temp_path
        image_name = os.path.basename(img_path)
    else:
        # interactive prompt fallback for user input
        try:
            user_path = input('Enter image path: ').strip()
        except Exception:
            user_path = ''

        if not user_path:
            print(json.dumps({"error": "No image provided. Provide image path or pipe image bytes into stdin."}))
            sys.exit(1)

        if not os.path.exists(user_path):
            print(json.dumps({"error": f"Image file not found: {user_path}"}))
            sys.exit(1)

        img_path = user_path
        image_name = os.path.basename(img_path)

# ===============================
# 3. LOAD & PREPROCESS IMAGE
# ===============================
img = cv2.imread(img_path)

if img is None:
    print(json.dumps({"error": "Unable to load image"}))
    sys.exit(1)

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_resized = cv2.resize(img_rgb, (224, 224))
img_normalized = img_resized / 255.0
img_input = np.expand_dims(img_normalized, axis=0)

# ===============================
# 4. PREDICT
# ===============================
pred = model.predict(img_input, verbose=0)
predicted_class_idx = np.argmax(pred)
confidence = float(pred[0][predicted_class_idx] * 100)

# Get class labels from dataset directory
dataset_path = os.path.join(BASE_DIR, 'test')
if not os.path.exists(dataset_path):
    dataset_path = os.path.join(BASE_DIR, 'test')
class_labels = sorted([d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))])
predicted_label = class_labels[predicted_class_idx]

# ===============================
# 5. OUTPUT RESULT AS JSON
# ===============================
result = {
    "success": True,
    "image_name": image_name,
    "predicted_disease": predicted_label,
    "disease": predicted_label,
    "confidence": confidence / 100,
    "confidence_percent": f"{confidence:.2f}%",
    "all_predictions": {
        class_labels[i]: float(pred[0][i] * 100) 
        for i in range(len(class_labels))
    }
}

print(json.dumps(result))

# clean up temporary file if used
if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
    try:
        os.remove(temp_file)
    except Exception:
        pass


