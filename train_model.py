import pandas as pd
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from tensorflow.keras.losses import CategoricalCrossentropy
from pathlib import Path
import sys
import numpy as np

# ===============================
# 1. LOAD CSV FILES
# ===============================

BASE_DIR = Path(__file__).parent
TRAIN_CSV = BASE_DIR / "train.csv"
TEST_CSV = BASE_DIR / "test.csv"

if not TRAIN_CSV.exists() or not TEST_CSV.exists():
    print(f"Expected CSV files at: {TRAIN_CSV} and {TEST_CSV}")
    print("Make sure your `train.csv` and `test.csv` are in the script directory.")
    sys.exit(1)

train_df = pd.read_csv(str(TRAIN_CSV))
test_df = pd.read_csv(str(TEST_CSV))

# Ensure path and label columns are strings and drop any rows with missing values
if 'location' in train_df.columns:
    train_df['location'] = train_df['location'].astype(str)
if 'label' in train_df.columns:
    train_df['label'] = train_df['label'].astype(str)
train_df = train_df.dropna(subset=['location', 'label'])

if 'location' in test_df.columns:
    test_df['location'] = test_df['location'].astype(str)
if 'label' in test_df.columns:
    test_df['label'] = test_df['label'].astype(str)
test_df = test_df.dropna(subset=['location', 'label'])

print("Train samples:", len(train_df))
print("Test samples:", len(test_df))

# ===============================
# 2. IMAGE DATA GENERATORS
# ===============================

IMG_SIZE = (224, 224)
BATCH_SIZE = 8  # Reduced batch size for better gradient updates

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    zoom_range=0.3,
    horizontal_flip=True,
    vertical_flip=True,
    shear_range=0.2,
    fill_mode='nearest'
)

test_datagen = ImageDataGenerator(rescale=1./255)

train_data = train_datagen.flow_from_dataframe(
    train_df,
    x_col="location",
    y_col="label",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

test_data = test_datagen.flow_from_dataframe(
    test_df,
    x_col="location",
    y_col="label",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

NUM_CLASSES = len(train_data.class_indices)
print("Number of classes:", NUM_CLASSES)

# ===============================
# 3. PRE-DEFINED MODEL (TRANSFER LEARNING)
# ===============================

base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)

# Unfreeze most pre-trained layers (keep only first 10 frozen)
for layer in base_model.layers[:10]:
    layer.trainable = False
for layer in base_model.layers[10:]:
    layer.trainable = True

# Custom classification layers with L2 regularization
from tensorflow.keras.regularizers import l2

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(512, activation="relu", kernel_regularizer=l2(1e-4))(x)
x = BatchNormalization()(x)
x = Dropout(0.5)(x)
x = Dense(256, activation="relu", kernel_regularizer=l2(1e-4))(x)
x = BatchNormalization()(x)
x = Dropout(0.4)(x)
x = Dense(128, activation="relu", kernel_regularizer=l2(1e-4))(x)
x = Dropout(0.3)(x)
output = Dense(NUM_CLASSES, activation="softmax")(x)

model = Model(inputs=base_model.input, outputs=output)

# Use lower learning rate for fine-tuning with label smoothing
optimizer = Adam(learning_rate=5e-5)
model.compile(
    optimizer=optimizer,
    loss=CategoricalCrossentropy(label_smoothing=0.1),
    metrics=["accuracy"]
)

model.summary()

# ===============================
# 4. TRAIN THE MODEL
# ===============================

EPOCHS = 9  # Increased for better convergence to 80% target

# Compute class weights to help with imbalanced classes
try:
    classes_array = np.array(train_data.classes)
    unique, counts = np.unique(classes_array, return_counts=True)
    total = counts.sum()
    class_weight = {int(cls): float(total) / (len(unique) * cnt) for cls, cnt in zip(unique, counts)}
    print("Using class weights:", class_weight)
except Exception as e:
    print("Could not compute class weights automatically:", e)
    class_weight = None

# Callbacks for adaptive learning rate and early stopping
callbacks = [
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=1, min_lr=1e-6, verbose=1),
    EarlyStopping(monitor='val_accuracy', patience=2, restore_best_weights=True, verbose=1)
]

history = model.fit(
    train_data,
    validation_data=test_data,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks
)

# ===============================
# 5. SAVE TRAINED MODEL
# ===============================

model.save("skin_disease_model.h5")
print("Model saved successfully as skin_disease_model.h5")

# ===============================
# 6. FINAL ACCURACY
# ===============================

train_acc = history.history["accuracy"][-1]
val_acc = history.history["val_accuracy"][-1]

print(f"Final Training Accuracy: {train_acc * 100:.2f}%")
print(f"Final Validation Accuracy: {val_acc * 100:.2f}%")
