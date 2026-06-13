import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2, EfficientNetB0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization, Input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import SGD, Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping, ModelCheckpoint
from tensorflow.keras.losses import CategoricalCrossentropy
from pathlib import Path
import sys

print("=" * 80)
print("SKIN DISEASE DETECTION - OPTIMIZED TRAINING")
print("=" * 80)

# ===============================
# 1. LOAD CSV FILES
# ===============================
BASE_DIR = Path(__file__).parent
TRAIN_CSV = BASE_DIR / "train.csv"
TEST_CSV = BASE_DIR / "test.csv"

if not TRAIN_CSV.exists() or not TEST_CSV.exists():
    print(f"ERROR: CSV files not found at {TRAIN_CSV} and {TEST_CSV}")
    sys.exit(1)

train_df = pd.read_csv(str(TRAIN_CSV))
test_df = pd.read_csv(str(TEST_CSV))

# Clean data
train_df['location'] = train_df['location'].astype(str)
train_df['label'] = train_df['label'].astype(str)
train_df = train_df.dropna(subset=['location', 'label'])

test_df['location'] = test_df['location'].astype(str)
test_df['label'] = test_df['label'].astype(str)
test_df = test_df.dropna(subset=['location', 'label'])

print(f"✓ Train samples: {len(train_df)}")
print(f"✓ Test samples: {len(test_df)}")

# ===============================
# 2. AGGRESSIVE DATA AUGMENTATION
# ===============================
IMG_SIZE = (224, 224)
BATCH_SIZE = 16

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=45,
    width_shift_range=0.25,
    height_shift_range=0.25,
    shear_range=0.25,
    zoom_range=0.4,
    brightness_range=(0.6, 1.4),
    horizontal_flip=True,
    vertical_flip=True,
    fill_mode='nearest'
)

test_datagen = ImageDataGenerator(rescale=1./255)

train_data = train_datagen.flow_from_dataframe(
    train_df,
    x_col="location",
    y_col="label",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    shuffle=True,
    seed=42
)

test_data = test_datagen.flow_from_dataframe(
    test_df,
    x_col="location",
    y_col="label",
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    shuffle=False
)

NUM_CLASSES = len(train_data.class_indices)
print(f"✓ Number of classes: {NUM_CLASSES}")

# ===============================
# 3. BUILD OPTIMIZED MODEL
# ===============================
print("\n[MODEL ARCHITECTURE]")

# Use EfficientNetB0 (better than MobileNetV2 for accuracy)
base_model = EfficientNetB0(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)

# Unfreeze all layers for fine-tuning
for layer in base_model.layers:
    layer.trainable = True

# Custom dense layers
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = BatchNormalization()(x)
x = Dense(512, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4))(x)
x = BatchNormalization()(x)
x = Dropout(0.5)(x)
x = Dense(256, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4))(x)
x = BatchNormalization()(x)
x = Dropout(0.4)(x)
x = Dense(128, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(1e-4))(x)
x = Dropout(0.3)(x)
output = Dense(NUM_CLASSES, activation="softmax")(x)

model = Model(inputs=base_model.input, outputs=output)

# Compile with SGD (better convergence than Adam for transfer learning)
optimizer = SGD(learning_rate=1e-3, momentum=0.9, nesterov=True)
model.compile(
    optimizer=optimizer,
    loss=CategoricalCrossentropy(label_smoothing=0.2),
    metrics=["accuracy"]
)

print(f"✓ Model built with EfficientNetB0 backbone")
print(f"✓ Total params: {model.count_params():,}")

# ===============================
# 4. COMPUTE CLASS WEIGHTS
# ===============================
print("\n[CLASS BALANCING]")
classes_array = train_data.classes
unique, counts = np.unique(classes_array, return_counts=True)
total = counts.sum()
class_weight = {int(cls): float(total) / (len(unique) * cnt) for cls, cnt in zip(unique, counts)}
print(f"✓ Class weights computed: {len(class_weight)} classes")

# ===============================
# 5. TRAIN THE MODEL
# ===============================
print("\n[TRAINING]")
EPOCHS = 15

callbacks = [
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-6, verbose=1),
    EarlyStopping(monitor='val_accuracy', patience=3, restore_best_weights=True, verbose=1),
    ModelCheckpoint('best_model.h5', monitor='val_accuracy', save_best_only=True, verbose=1)
]

history = model.fit(
    train_data,
    validation_data=test_data,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=callbacks,
    verbose=1
)

# ===============================
# 6. SAVE AND EVALUATE
# ===============================
print("\n[RESULTS]")
print("=" * 80)

# Save model
model.save("skin_disease_model_optimized.h5")
print("✓ Model saved as: skin_disease_model_optimized.h5")

# Final metrics
train_acc = history.history["accuracy"][-1] * 100
val_acc = history.history["val_accuracy"][-1] * 100
train_loss = history.history["loss"][-1]
val_loss = history.history["val_loss"][-1]

print(f"\n📊 FINAL METRICS:")
print(f"   Training Accuracy:   {train_acc:.2f}%")
print(f"   Validation Accuracy: {val_acc:.2f}%")
print(f"   Training Loss:       {train_loss:.4f}")
print(f"   Validation Loss:     {val_loss:.4f}")

# Best epoch
best_epoch = np.argmax(history.history['val_accuracy']) + 1
best_val_acc = np.max(history.history['val_accuracy']) * 100
print(f"\n🏆 BEST EPOCH: #{best_epoch} with {best_val_acc:.2f}% accuracy")

if val_acc >= 78:
    print("\n✅ TARGET ACHIEVED: Accuracy >= 78%")
else:
    print(f"\n⚠️  Target: 78%, Current: {val_acc:.2f}%")
    
print("=" * 80)
