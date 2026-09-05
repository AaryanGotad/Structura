import os
import zipfile
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import keras_hub

KERAS_FILE = "model/structura.keras"
EXTRACT_DIR = "model_extract"

# ==========================================
# 1. EXTRACT VOCABULARIES & WEIGHTS FROM ZIP
# ==========================================
os.makedirs(EXTRACT_DIR, exist_ok=True)

with zipfile.ZipFile(KERAS_FILE, "r") as z:
    # Extract BERT tokenizer vocabulary
    bert_vocab_path = z.extract(
        "assets/layers/bert_text_embedder_preprocessor/tokenizer/vocabulary.txt",
        EXTRACT_DIR
    )
    # Extract Character TextVectorization vocabulary
    char_vocab_path = z.extract(
        "assets/layers/text_vectorization/vocabulary.txt",
        EXTRACT_DIR
    )
    # Extract trained weights H5 file
    weights_path = z.extract("model.weights.h5", EXTRACT_DIR)

# ==========================================
# 2. RECONSTRUCT TOKEN BRANCH (MINILM)
# ==========================================
token_inputs = layers.Input(shape=(), dtype=tf.string, name='token_inputs')

# Reconstruct BertTokenizer from extracted vocabulary
tokenizer = keras_hub.tokenizers.BertTokenizer(
    vocabulary=bert_vocab_path,
    lowercase=True,
    strip_accents=False,
    split=True,
    suffix_indicator="##",
    oov_token="[UNK]"
)

preprocessor = keras_hub.models.BertTextEmbedderPreprocessor(
    tokenizer=tokenizer,
    sequence_length=256,
    truncate="round_robin"
)

backbone = keras_hub.models.BertBackbone.from_preset("all_minilm_l6_v2_en")

embedder = keras_hub.models.BertTextEmbedder(
    backbone=backbone,
    preprocessor=preprocessor,
    pooling_mode="mean",
    normalize=True,
    name="token_embedder"
)
embedder.trainable = False

preprocessed_tokens = embedder.preprocessor(token_inputs)
token_embeddings = embedder(preprocessed_tokens)

token_outputs = layers.Dense(128, activation='relu', name='dense')(token_embeddings)

token_model = tf.keras.Model(inputs=token_inputs, outputs=token_outputs, name='token_model')

# ==========================================
# 3. RECONSTRUCT CHARACTER BRANCH
# ==========================================
char_inputs = layers.Input(shape=(1,), dtype=tf.string, name='char_inputs')

# Load character vocabulary extracted from the archive
with open(char_vocab_path, "r", encoding="utf-8") as f:
    char_vocab = [line.strip() for line in f if line.strip()]

char_vectorizer = layers.TextVectorization(
    name="text_vectorization",
    output_mode="int"
)
char_vectorizer.set_vocabulary(char_vocab)

char_vectors = char_vectorizer(char_inputs)

# ✅ FIX: Hardcode input_dim to 70 to match the saved weights shape
char_embed = layers.Embedding(
    input_dim=70, 
    output_dim=25,
    name="embedding"
)
char_embeddings = char_embed(char_vectors)

char_bi_lstm = layers.Bidirectional(
    layers.LSTM(32),
    name="bidirectional"
)(char_embeddings)

char_model = tf.keras.Model(inputs=char_inputs, outputs=char_bi_lstm, name='char_model')

# ==========================================
# 4. RECONSTRUCT POSITIONAL BRANCHES
# ==========================================
# Line number model
line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
x = layers.Dense(32, activation='relu', name='dense_1')(line_number_inputs)
line_number_model = tf.keras.Model(inputs=line_number_inputs, outputs=x, name='line_number_model')

# Total lines model
total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
y = layers.Dense(32, activation='relu', name='dense_2')(total_lines_inputs)
total_line_model = tf.keras.Model(inputs=total_lines_inputs, outputs=y, name='total_line_model')

# ==========================================
# 5. COMBINE BRANCHES & CLASSIFICATION HEAD
# ==========================================
combined_embeddings = layers.Concatenate(
    name='tokne_char_hybrid_embedding'
)([token_model.output, char_model.output])

z = layers.Dense(256, activation='relu', name='dense_3')(combined_embeddings)
z = layers.Dropout(0.5, name='dropout')(z)

z = layers.Concatenate(
    name='token_char_positional_embedding'
)([line_number_model.output, total_line_model.output, z])

output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

# Reassemble full model
model_3_reconstructed = tf.keras.Model(
    inputs=[
        line_number_model.input,
        total_line_model.input,
        token_model.input,
        char_model.input
    ],
    outputs=output_layer,
    name='model_3'
)

# ==========================================
# 6. RESTORE TRAINED WEIGHTS
# ==========================================
print("Loading trained weights from model.weights.h5...")
# Fixed line for Keras 3 format
model_3_reconstructed.load_weights(weights_path, skip_mismatch=True)
print("Successfully loaded trained weights!")

# ==========================================
# 7. TEST INFERENCE VERIFICATION
# ==========================================
sample_line = tf.one_hot([0], depth=15)
sample_total = tf.one_hot([5], depth=20)
# ✅ FIX: Pass text data as tf.constant string tensors instead of NumPy arrays
sample_token = tf.constant(["Patients with diabetes showed improved outcomes."])
sample_char = tf.constant([["P a t i e n t s   w i t h   d i a b e t e s"]])

preds = model_3_reconstructed.predict([
    sample_line,
    sample_total,
    sample_token,
    sample_char
])

print("\n--- Inference Test Output ---")
print("Prediction Probabilities:", preds)
print("Predicted Class Index:", np.argmax(preds, axis=1)[0])