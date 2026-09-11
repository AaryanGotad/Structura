from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from pathlib import Path
import os
import zipfile
import sys

import tensorflow as tf
from tensorflow.keras import layers
import keras_hub

import utilities.utils as utils

app = FastAPI()

class AlternativePrediction(BaseModel):
    predictedClass: str
    confidence: float


class StructureResult(BaseModel):
    text: str
    predictedClass: str
    confidence: float
    alternative: AlternativePrediction
    rawScores: list[float]


class AnalyzeResponse(BaseModel):
    success: bool
    data: list[StructureResult]
    rawOutput: str


class AnalyzeRequest(BaseModel):
    text: str

def load_structura_model():
    """
    Load the pre-trained Structura model weights from the specified Keras file.
    Assets and weights are extracted from the Keras file, and the model architecture is reconstructed.
    """
    CURR_DIR = Path(__file__).resolve().parent
    keras_file_path = CURR_DIR / 'model' / 'structura.keras'
    extract_dir = CURR_DIR / "model_extract"

    os.makedirs(extract_dir, exist_ok=True)

    # 1. EXTRACT VOCABULARIES & WEIGHTS FROM ZIP
    with zipfile.ZipFile(keras_file_path, "r") as z:
        bert_vocab_path = z.extract(
            "assets/layers/bert_text_embedder_preprocessor/tokenizer/vocabulary.txt",
            extract_dir
        )
        char_vocab_path = z.extract(
            "assets/layers/text_vectorization/vocabulary.txt",
            extract_dir
        )
        weights_path = z.extract("model.weights.h5", extract_dir)

    # RECONSTRUCT TOKEN BRANCH (MINILM)
    token_inputs = layers.Input(shape=(), dtype=tf.string, name="token_inputs")

    tokenizer = keras_hub.tokenizers.BertTokenizer(
        vocabulary=bert_vocab_path,
        lowercase=True,
        strip_accents=True,
        split=True,
        suffix_indicator="##",
        oov_token="[UNK]",
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
    token_outputs = layers.Dense(128, activation="relu", name='dense')(token_embeddings)
    token_model = tf.keras.Model(
        inputs=token_inputs,
        outputs=token_outputs,
        name="token_model"
    )

    # RECONSTRUCT CHARACTER BRANCH
    char_inputs = layers.Input(shape=(1,), dtype=tf.string, name="char_inputs")

    with open(char_vocab_path, "r", encoding="utf-8") as f:
        char_vocab = [line.strip() for line in f if line.strip() and line.strip() != "[UNK]"]

    char_vectorizer = layers.TextVectorization(
        name='text_vectorization',
        output_mode='int',
    )
    char_vectorizer.set_vocabulary(char_vocab)

    char_vectors = char_vectorizer(char_inputs)
    char_embed = layers.Embedding(
        input_dim=70,
        output_dim=25,
        name='embedding'
    )
    char_embeddings = char_embed(char_vectors)

    char_bi_lstm = layers.Bidirectional(
        layers.LSTM(32),
        name='bidrectional'
    )(char_embeddings)

    char_model = tf.keras.Model(
        inputs=char_inputs,
        outputs=char_bi_lstm,
        name="char_model"
    )

    # RECONSTRUCT POSITIONAL BRANCHES
    line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name="line_number_input")
    x = layers.Dense(32, activation="relu", name='dense_1')(line_number_inputs)
    line_number_model = tf.keras.Model(
        inputs=line_number_inputs,
        outputs=x,
        name="line_number_model"
    )

    total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name="total_lines_input")
    y = layers.Dense(32, activation="relu", name='dense_2')(total_lines_inputs)
    total_line_model = tf.keras.Model(
        inputs=total_lines_inputs,
        outputs=y,
        name="total_line_model"
    )

    # COMBINE BRANCHES & CLASSIFICATION HEAD
    combined_embeddings = layers.Concatenate(
        name="token_char_hybrid_embedding"
    )([token_model.output, char_model.output])

    z = layers.Dense(256, activation='relu', name='dense_3')(combined_embeddings)
    z = layers.Dropout(0.5, name='dropout')(z)

    z = layers.Concatenate(
        name='token_char_positional_embedding'
    )([line_number_model.output, total_line_model.output, z])

    output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

    # REASSEMBLE FULL MODEL
    model = tf.keras.Model(
        inputs=[
            line_number_model.input,
            total_line_model.input,
            token_model.input,
            char_model.input
        ],
        outputs=output_layer,
        name="structura_model"
    )

    # RESTORE TRAINED WEIGHTS
    model.load_weights(weights_path, skip_mismatch=True)

    return model

# MODEL INITIALIZATION
try:
    structura_model = load_structura_model()
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit(1)

@app.get('/')
def read_root():
    return {"message": "Welcome to the Text Analysis API!"}

@app.post('/analyze', response_model=AnalyzeResponse)
def analyze_text(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze the input text and return the predicted structure along with confidence scores.
    """
    try:
        abstract_line_numbers_one_hot, abstract_total_lines_one_hot, abstract_lines, abstract_chars = utils.preprocess_text(request.text)
    
        if abstract_lines is None or abstract_chars is None:
            raise HTTPException(status_code=400, detail="Invalid input text. Please provide a valid abstract.")
    
        # pass inputs to the model for prediction
        predictions_probs = structura_model.predict(x=(
            abstract_line_numbers_one_hot,
            abstract_total_lines_one_hot,
            tf.constant(abstract_lines),
            tf.expand_dims(tf.constant(abstract_chars), axis=-1)
        ))
    
        # formatted output
        formatted_output = utils.data_formatting(predictions_probs, abstract_lines)

        output = utils.response_formatting(
            formatted_output,
            success=True,
            rawOutput=str(predictions_probs)
        )
    
        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))