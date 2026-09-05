import tensorflow as tf
from pathlib import Path
from spacy.lang.en import English

class_names_path = Path(__file__).with_name('class_names.txt')

with class_names_path.open('r', encoding='utf=8') as file:
    class_names = file.read().splitlines()

def split_chars(text):
    """
    Splits the input text into individual characters and returns them as a space-separated string.
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

    # -----------( ONE-HOT ENCODING L.N.s & T.L.s )-----------
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

def output_formatting(model_pred_probs, abstract_lines, class_names=class_names):
    """
    Formats the model's prediction probabilities into a structured output format.
    """
    # turning prediction probabilities into prediction classes
    abstract_preds = tf.argmax(model_pred_probs, axis=1)

    # turning prediction class integers into string class names
    abstract_pred_classes = [class_names[i] for i in abstract_preds]

    formatted_lines = []
    for i, line in enumerate(abstract_lines):
        formatted_line = {}
        formatted_line['label'] = abstract_pred_classes[i]
        formatted_line['text'] = line
        formatted_lines.append(formatted_line)

    return formatted_lines
