# import streamlit as st

# import tensorflow as tf
# import keras_hub

# import utilities.utils as utilities
# from pathlib import Path
# import threading

# import tensorflow as tf
# import keras_hub

import keras_hub

import tensorflow as tf
import keras_hub
import zipfile
import os

# # --------------------------------------------------
# # Recover tokenizer vocabulary from structura.keras
# # --------------------------------------------------

# MODEL_PATH = "model/structura.keras"
# EXTRACT_DIR = "model_extract"

# with zipfile.ZipFile(MODEL_PATH, "r") as z:
#     z.extract(
#         "assets/layers/bert_text_embedder_preprocessor/tokenizer/vocabulary.txt",
#         EXTRACT_DIR
#     )

# vocab_path = os.path.join(
#     EXTRACT_DIR,
#     "assets",
#     "layers",
#     "bert_text_embedder_preprocessor",
#     "tokenizer",
#     "vocabulary.txt"
# )

# print("Vocabulary exists:", os.path.exists(vocab_path))

# # --------------------------------------------------
# # Reconstruct MiniLM
# # --------------------------------------------------

# backbone = keras_hub.models.BertBackbone.from_preset(
#     "all_minilm_l6_v2_en"
# )

# tokenizer = keras_hub.tokenizers.BertTokenizer(
#     vocabulary=vocab_path,
#     lowercase=True,
#     strip_accents=False,
#     split=True,
#     suffix_indicator="##",
#     oov_token="[UNK]",
# )

# preprocessor = keras_hub.models.BertTextEmbedderPreprocessor(
#     tokenizer=tokenizer,
#     sequence_length=256,
#     truncate="round_robin"
# )

# embedder = keras_hub.models.BertTextEmbedder(
#     backbone=backbone,
#     preprocessor=preprocessor,
#     pooling_mode="mean",
#     normalize=True
# )

# # --------------------------------------------------
# # Test
# # --------------------------------------------------

# sample = [
#     "Patients with diabetes had increased cardiovascular risk."
# ]

# processed = embedder.preprocessor(sample)
# embedding = embedder(processed)

# print("Embedding shape:", embedding.shape)

# print("Pooling:", embedder.pooling_mode)
# print("Normalize:", embedder.normalize)
# print("Vocabulary size:", embedder.backbone.vocabulary_size)
# print("Layers:", embedder.backbone.num_layers)
# print("Hidden dim:", embedder.backbone.hidden_dim)

# # 1. Load the MiniLM backbone architecture + pretrained weights
# backbone = keras_hub.models.BertBackbone.from_preset(
#     "all_minilm_l6_v2_en"
# )

# # 2. Reuse the vocabulary recovered from your .keras file
# tokenizer = keras_hub.tokenizers.BertTokenizer(
#     vocabulary=vocab_path,
#     lowercase=True,
#     strip_accents=False,
#     split=True,
#     suffix_indicator="##",
#     oov_token="[UNK]",
# )

# # 3. Reconstruct the exact preprocessor configuration
# preprocessor = keras_hub.models.BertTextEmbedderPreprocessor(
#     tokenizer=tokenizer,
#     sequence_length=256,
#     truncate="round_robin"
# )

# # 4. Construct the TextEmbedder manually
# embedder = keras_hub.models.BertTextEmbedder(
#     backbone=backbone,
#     preprocessor=preprocessor,
#     pooling_mode="mean",
#     normalize=True
# )

# print(backbone)
# print(embedder)

token_inputs = layers.Input(
    shape=(),
    dtype='string',
    name='token_inputs'
)

preprocessed_tokens = embedder.preprocessor(token_inputs)
token_embeddings = embedder(preprocessed_tokens)
token_outputs = layers.Dense(
    128,
    activation='relu'
)(token_embeddings)

token_model = tf.keras.Model(
    inputs=token_inputs,
    outputs=token_outputs
)

# MODEL_LOCK = threading.Lock()

# @st.cache_resource
# def load_model():
#     """
#     Loads a TensorFlow SavedModel from the specified path and returns the loaded model.
#     The function ensures that the model is loaded onto the CPU for inference.
#     """
#     tf.keras.backend.clear_session()  # clear any existing models from memory

#     CURR_DIR = Path(__file__).resolve().parent
#     model_path = CURR_DIR / "model" / "structura.keras"

#     # loading the SavedModel directory, ensuring all components are loaded to CPU
#     with tf.device('/CPU:0'):
#         model = tf.keras.models.load_model(model_path)

#     return model

# left_col, middle_col, right_col = st.columns([1, 2, 1])

# with middle_col:
#     # initializing model
#     try:
#         with st.spinner('Loading Model...'):
#             model = load_model()
#     except Exception as exc:
#         st.error(f"Failed to load model: {exc}")
#         st.stop()       

# # -----------------( TITLE & HEADING )-----------------
# st.markdown(
#     """
#         <h1 
#             style='text-align: center;
#                    font-size: 4rem;
#                    letter-spacing: 0.03rem;
#                    font-family: "Copperplate";
#                    text-decoration: underline;
#                    margin-bottom: 0.05em;'>
#             Structura
#         </h1>
#     """,
#     unsafe_allow_html=True)

# st.markdown(
#     """
#         <h2 
#             style='text-align: center;
#                     font-size: 1.95rem;
#                     letter-spacing: 0.15rem;
#                     font-family: "Roboto";'>
#             Understand what the Reasearch is About
#         </h2>
#     """,
#     unsafe_allow_html=True)

# # -----------------( INPUT )-----------------
# def clear_text():
#     """
#     Clears the text area input by setting its value to an empty string.
#     This function is used as a callback for the "Clear" button in the Streamlit app.
#     """
#     st.session_state['abstract_input'] = ''

# st.text_area(
#     label="Paste Abstract Here",
#     placeholder="Paste abstract of a research paper here...",
#     height='content',
#     key="abstract_input"
# )

# st.button("Clear", on_click=clear_text)


# # -----------------( OUTPUT )-----------------
# abstract_line_numbers_one_hot, abstract_total_lines_one_hot, abstract_lines, abstract_chars = utilities.preprocess_text(st.session_state['abstract_input'])

# if not abstract_lines:
#     st.info('Paste an abstract to structure it.')
#     st.stop()

# with st.spinner('Structuring...'):
#     with tf.device('/CPU:0'):
#         # model_pred_probs = model(
#         #     {
#         #         'line_number_input': abstract_line_numbers_one_hot,
#         #         'total_lines_input': abstract_total_lines_one_hot,
#         #         'token_inputs': tf.constant(abstract_lines),
#         #         'char_inputs': tf.expand_dims(tf.constant(abstract_chars), axis=-1),
#         #     },
#         #     training=False,
#         # )
#         model_pred_probs = model.predict(x=(abstract_line_numbers_one_hot,
#                                             abstract_total_lines_one_hot,
#                                             tf.constant(abstract_lines),
#                                             tf.expand_dims(tf.constant(abstract_chars), axis=-1)))

# output = utilities.output_formatting(model_pred_probs, abstract_lines)

# output
   