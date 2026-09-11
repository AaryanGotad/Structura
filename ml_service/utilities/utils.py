import tensorflow as tf
from spacy.lang.en import English

from pathlib import Path
from pydantic import BaseModel
import re

class_names_path = Path(__file__).with_name("class_names.txt")

with class_names_path.open("r", encoding="utf-8") as file:
    CLASS_NAMES = file.read().splitlines()

class AlternativePrediction(BaseModel):
    predictedClass: str
    confidence: float

class StructureResult(BaseModel):
    text: str
    predictedClass: str
    confidence: float
    alternative: AlternativePrediction
    rawScores: list[float]

def split_chars(text):
    """
    Splits the input text into individual characters and returns them as a single string with spaces in between.
    """
    return " ".join(list(text))

def preprocess_text(text):
    """
    Preprocesses the input text by performing the following steps:
    1. Sentence tokenization using spaCy's sentencizer.
    2. Creating a list of dictionaries containing line number and total lines for each sentence.
    3. One-hot encoding the line numbers and total lines.
    4. Splitting each sentence into individual characters.

    Args:
    - text: Input text to be preprocessed.

    Returns:
    - abstract_line_numbers_one_hot: One-hot encoded line numbers.
    - abstract_total_lines_one_hot: One-hot encoded total lines.
    - abstract_lines: List of sentences.
    - abstract_chars: List of sentences split into individual characters.
    """
    # -----------( SENTENCIZER )-----------
    nlp = English() # setup English sentence parser
    sentencizer = nlp.add_pipe('sentencizer') # create sentencizer splitting pipeline object

    # creating a 'doc' of parsed sequences
    doc = nlp(text)
    abstract_lines = [str(sent) for sent in list(doc.sents)]

    # -----------( LINE NUMBER & TOTAL NO. OF LINES )-----------
    total_lines = len(abstract_lines)

    # going through each line in abstract and creating a list dictionaries
    # containing features for each line
    lines = []
    for i, line in enumerate(abstract_lines):
        line_dict = {}
        line_dict['text'] = str(line)
        line_dict['line_number'] = i
        line_dict['total_lines'] = total_lines - 1
        lines.append(line_dict)

    # -----------( ONE-HOT ENCODING L.Ns & T.Ls )-----------
    # getting all line_number values from text abstract and one-hot endoding them
    line_numbers = [line['line_number'] for line in lines]
    abstract_line_numbers_one_hot = tf.one_hot(line_numbers, depth=15)

    # getting all total_lines values from text abstract and one-hot encoding them
    total_lines_values = [line['total_lines'] for line in lines]
    abstract_total_lines_one_hot = tf.one_hot(total_lines_values, depth=20)

    # -----------( CHARACTER SPLITTING )-----------
    # splitting each line into individual characters
    abstract_chars = [split_chars(line) for line in abstract_lines]

    return abstract_line_numbers_one_hot, abstract_total_lines_one_hot, abstract_lines, abstract_chars

def data_formatting(model_pred_probs, abstract_lines, class_names=CLASS_NAMES, k=1):
    """
    Formats the model prediction probabilities into a structured output.
    """

    # turning prediction probabilities into prediction classes
    abstract_preds = tf.argmax(model_pred_probs, axis=1)

    # getting the alternate predictions and their corresponding class indices
    alt_probs, alt_indices = tf.math.top_k(model_pred_probs, k=2)

    # Build each result with its required primary and alternative prediction.
    line_predictions = []
    for i, line in enumerate(abstract_lines):
        primary_index = int(abstract_preds[i])
        alternative_index = int(alt_indices[i][k])
        line_predictions.append(
            StructureResult(
                text=line,
                predictedClass=class_names[primary_index],
                confidence=float(model_pred_probs[i][primary_index]),
                rawScores=[float(score) for score in model_pred_probs[i]],
                alternative=AlternativePrediction(
                    predictedClass=class_names[alternative_index],
                    confidence=float(alt_probs[i][k])
                )
            )
        )

    return line_predictions


def response_formatting(formatted_lines, success=True, rawOutput=None):
    """
    Formats the final response to be returned by the API.
    """
    return {
        "success": success,
        "data": formatted_lines,
        "rawOutput": rawOutput
    }
