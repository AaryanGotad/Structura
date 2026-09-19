This research paper is the source of my data and training goals
[PubMed 200k RCT](https://www.google.com/url?q=https%3A%2F%2Farxiv.org%2Fabs%2F1710.06071)

This research paper is the source of where my model architecture is inspired from
[neural networks for joint sentence classification in medical paper abstracts by dernoncourt, 2017](https://www.google.com/url?q=https%3A%2F%2Farxiv.org%2Fpdf%2F1612.05251.pdf)

I directly imported the data from the official github repo 
[](https://github.com/Franck-Dernoncourt/pubmed-rct)

Used the PubMed 20k dataset with numbers replaced with at sign. With the premade train test and validation splits.

Train set has 180,040 lines, val set has 30,212 lines, and test set has 30,135 lines.

Training set has the following class wise distribution, METHODS: 59353, RESULTS: 57953, CONCLUSIONS: 27168, BACKGROUND: 21727, OBJECTIVE: 13839.
OBJECTIVES class is the least common class which reflects in the model as well, as it is frequently confused between OBJECTIVE AND BACKGROUND.

I did a series of modelling experiments (All the experiments where done on 10% of the training data of pubmed 20k to keep the experiments short to choose the best architecutre to train on full data, however they where validatied on the complete dataset, and they were done on keras 2 because the tutorial book i was referencing to was using the older version, this came back to me hard later):
1. Model 0: the baseline
    ```python
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline

    # create a pipeline
    model_0 = Pipeline([
        ('tf-idf', TfidfVectorizer()),
        ('clf', MultinomialNB())
    ])

    # fit the pipeline to the training data
    model_0.fit(X=train_sentences,
                y=train_labels_encoded)
    ```

    A simple multinomial naive bayes algorithm. Got validation metrics of
    ```json
    {'accuracy': 72.1832384482987,
     'precision': 0.7186466952323352,
     'recall': 0.7218323844829869,
     'f1': 0.6989250353450294}
    ```

2. Model 1: Conv1D with token embeddings
    A rather simple model which used a custom text vectorizer,
    ```python
    max_tokens = 68000

    from tensorflow.keras.layers import TextVectorization

    text_vectorizer = TextVectorization(max_tokens=max_tokens, # number of words in the vocabulary
                                        output_sequence_length=55) # desired output length of vectorized sequences
    text_vectorizer.adapt(train_sentences)
    ```
    having the following configuration
    ```json
    {'name': 'text_vectorization',
     'trainable': True,
     'dtype': 'string',
     'batch_input_shape': (None,),
     'max_tokens': 68000,
     'standardize':     'lower_and_strip_punctuation',
     'split': 'whitespace',
     'ngrams': None,
     'output_mode': 'int',
     'output_sequence_length': 55,
     'pad_to_max_tokens': False,
     'sparse': False,
     'ragged': False,
     'vocabulary': None,
     'idf_weights': None,
     'encoding': 'utf-8',
     'vocabulary_size': 64841}
    ```

    And a custom text embedding layer to pair with it
    ```python
    token_embed = layers.Embedding(input_dim=len(rct_20k_text_vocab), # length of vocabulary
                               output_dim=128, # Note: different embedding sizes result in drastically different number of parameters to train
                               # Ysemasking to handle variable sequence lengths (saves space)
                               mask_zero=True,
                               name='token_embedding')
    ```

    I had label encoded the labels for my datasets, and converted them to tf.data API datasets,
    ```python
    train_dataset = tf.data.Dataset.from_tensor_slices((train_sentences, train_labels_one_hot))
    valid_dataset = tf.data.Dataset.from_tensor_slices((val_sentences, val_labels_one_hot))
    test_dataset = tf.data.Dataset.from_tensor_slices((test_sentences, test_labels_one_hot))

    train_dataset = train_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
    valid_dataset = valid_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
    test_dataset = test_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
    ```

    So the architecure became,
    ```python
    # create 1D convolutional model to process sequences
    inputs = layers.Input(shape=(1,), dtype=tf.string)

    text_vectors = text_vectorizer(inputs) # vectorize text inputs
    token_embeddings = token_embed(text_vectors) # create embedding

    x = layers.Conv1D(64, kernel_size=5, padding='same', activation='relu')(token_embeddings)
    x = layers.GlobalAveragePooling1D()(x) # condense the output of our feature vector

    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model_1 = tf.keras.Model(inputs, outputs)

    # compile
    model_1.compile(loss='categorical_crossentropy', # if your labels are integer type (not one hot) use sparse_categorical_crossentropy
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    This was my training setup,
    ```python
    # fit the model
    model_1_history = model_1.fit(train_dataset,
                                steps_per_epoch=int(0.1 * len(train_dataset)), # only fir on 10% of batches for faster training times
                                epochs=3,
                                validation_data=valid_dataset,
                                validation_steps=int(0.1 * len(valid_dataset))) # only validate on 10% of batches
    ```
    And these are the validation metrics,
    ```json
    {'accuracy': 78.70713623725672,
     'precision': 0.7843097834920143,
     'recall': 0.7870713623725671,
     'f1': 0.7846874516371526}
     ```

3. Model 2: Feature extraction with pretrained token embeddings
    Here i replaced the custom text vectorizer and embedder with the Universal Sentence Encoder from tensorflow_hub
    ```py
    import tensorflow_hub as hub
    tf_hub_embedding_layer = hub.KerasLayer("https://tfhub.dev/google/universal-sentence-encoder/4",
                                            trainable=False,
                                            name="universal_sentence_encoder")
    ```

    hence now the model architecture became,
    ```py
    # define feature extractor model using TF Hub layer
    inputs = layers.Input(shape=[], dtype=tf.string)

    pretrained_embedding = tf_hub_embedding_layer(inputs) # tokenize text and create embedding

    x = layers.Dense(128, activation='relu')(pretrained_embedding) # add a fully connected layer on top of the embedding
    # Note: we can add more layers here if we want to

    outputs = layers.Dense(5, activation='softmax')(x) # create the output layer

    model_2 = tf.keras.Model(inputs=inputs,
                            outputs=outputs)

    # compile the model
    model_2.compile(loss='categorical_crossentropy',
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    trained it for 3 epochs with the same training setup as previous experiment and this is the validation score,
    ```json
    {'accuracy': 71.51793989143387,
     'precision': 0.7155376013152608,
     'recall': 0.7151793989143387,
     'f1': 0.7122709045787224}
    ```

4. Model 3. Conv1D with character embeddings
    here i experimented with a new type of input to the model, character level input, now the model took an abstract line and split it into individual characters like this,
    ```py
    " ".join(list(text))
    ```

    Trained a simple custom character vectorizer and adapted it to the training data
    ```py
    import string
    alphabet = string.ascii_lowercase + string.digits + string.punctuation
    NUM_CHAR_TOKENS = len(alphabet) + 2 # num characters in alphabet + space + OOV token
    char_vectorizer = TextVectorization(max_tokens=NUM_CHAR_TOKENS,
                                        output_sequence_length=output_seq_char_len,
                                        standardize='lower_and_strip_punctuation',
                                        name='char_vectorizer')

    # adapt character vectorizer to training characters
    char_vectorizer.adapt(train_chars)

    char_embed = layers.Embedding(input_dim=NUM_CHAR_TOKENS, # number of different characters
                                output_dim=25, # embedding dimension of each character (same as Figure 1 in https://arxiv.org/pdf/1612.05251.pdf)
                                mask_zero=False, # don't use masks (this messes up model_5 if set to True)
                                name='char_embed')
    ```
    Model architecture,
    ```py
    # make Conv!d on chars only
    inputs = layers.Input(shape=(1,), dtype='string')

    char_vectors = char_vectorizer(inputs)
    char_embeddings = char_embed(char_vectors)

    x = layers.Conv1D(64, kernel_size=5, padding='same', activation='relu')(char_embeddings)
    x = layers.GlobalMaxPool1D()(x)

    outputs = layers.Dense(num_classes, activation='softmax')(x)

    model_3 = tf.keras.Model(inputs=inputs,
                            outputs=outputs,
                            name='model_3_conv1D_char_embedding')

    # compile model

    model_3.compile(loss='categorical_crossentropy',
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    With the same setup as last time, trained for 3 epochs, got the validation metrics as
    ```json
    {'accuracy': 64.82192506288892,
     'precision': 0.6427506806720115,
     'recall': 0.6482192506288892,
     'f1': 0.6366563976108488}
    ```

    Yes... that is the worst ive had yet

5. Model 4. Combining pretrained token embedding + character embeddings (hybrid embedding layer)
    This is where the architecture started to become complex and similar looking like the research paper
    ```py
    # 1. setup token inputs/model
    token_inputs = layers.Input(shape=[], dtype=tf.string, name='token_input')
    token_embeddings = tf_hub_embedding_layer(token_inputs)
    token_output = layers.Dense(128, activation='relu')(token_embeddings)
    token_model = tf.keras.Model(inputs=token_inputs,
                                outputs=token_output)

    # 2. setup char inputs/model
    char_inputs = layers.Input(shape=(1,), dtype='string', name='char_input')
    char_vectors = char_vectorizer(char_inputs)
    char_embeddings = char_embed(char_vectors)
    char_bi_lstm = layers.Bidirectional(layers.LSTM(25))(char_embeddings) # bi-LSTM showin in Figure 1 of https://arxiv.org/pdf/1612.05251.pdf
    char_model = tf.keras.Model(inputs=char_inputs,
                                outputs=char_bi_lstm)

    # 3. Concatenate token and char inputs (create hybrid token embedding)
    token_char_concat = layers.Concatenate(name='token_char_hybrid')([token_model.output,
                                                                    char_model.output])
    # 4. create output layers - addition of dropout discussed in 4.2 of https://arxiv.org/pdf/1612.05251.pdf
    combined_dropout = layers.Dropout(0.5)(token_char_concat)
    combined_dense = layers.Dense(200, activation='relu')(combined_dropout) # slightly different to Figure 1 due to different shapes of token/char embedding layers
    final_dropout = layers.Dropout(0.5)(combined_dense)
    output_layer = layers.Dense(num_classes, activation='softmax')(final_dropout)

    # 5. Construct model with char and token inputs
    model_4 = tf.keras.Model(inputs=[token_model.input, char_model.input],
                            outputs=output_layer,
                            name='model_4_token_and_char_embeddings')

    # compile token char model
    model_4.compile(loss='categorical_crossentropy',
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    At this point my model size got really big (960.04 MB) more than 10-15 times the size of any model yet, this is where my problems where about to start i just hadn't realized them yet
    Trained for 3 epochs with the same setup and got the following results (oh and a PS. i had been updating the dataset along side it constantly with the different data needs lieke characters line numbers, etc. so dont worry about dataset not being accurate).
    Validation accuracy came as
    ```json
    {'accuracy': 73.47742618826956,
     'precision': 0.7346182206903871,
     'recall': 0.7347742618826956,
     'f1': 0.7311011567951835}
    ```

4. Model 5. Transfer Learning with pretrained token embeddings + character embeddings + positional embeddings
    Added two positional embeddings of line number and total lines which tells which line is currently in the input from abstract, and what are the total lines in the abstract respectively. I did not keep these columns numerical, i one hot encoded them using tensorflows one hot method, to the depths of 15 and 20 respectively, these are not random depths, these values cover 98% of the line_number and total_lines column respectively, meaning most abstarcts in the training data contain not more than 20 lines, where each line contains a positional encoding of 15 or less. This also reveals a limitation that the model is not good at predicting on long abstracts. The values of depth of line numbers and total lines one hot column stay the same here on.
    And this is the point where the architecture from research paper is being completely implemented by my using universal sentence encoder instead of the GloVe embeddings used in the paper.
    Here is the architecture,
    ```py
    # 1. Token inputs
    token_inputs = layers.Input(shape=[], dtype='string', name='token_inputs')
    token_embeddings = tf_hub_embedding_layer(token_inputs)
    token_outputs = layers.Dense(128, activation='relu')(token_embeddings)
    token_model = tf.keras.Model(inputs=token_inputs,
                                outputs=token_outputs)

    # 2. Char inputs
    char_inputs = layers.Input(shape=(1,), dtype='string', name='char_inputs')
    char_vectors = char_vectorizer(char_inputs)
    char_embeddings = char_embed(char_vectors)
    char_bi_lstm = layers.Bidirectional(layers.LSTM(32))(char_embeddings)
    char_model = tf.keras.Model(inputs=char_inputs,
                                outputs=char_bi_lstm)

    # 3. Line numbers inputs
    line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
    x = layers.Dense(32, activation='relu')(line_number_inputs)
    line_number_model = tf.keras.Model(inputs=line_number_inputs,
                                    outputs=x)

    # 4. Total lines inputs
    total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
    y = layers.Dense(32, activation='relu')(total_lines_inputs)
    total_line_model = tf.keras.Model(inputs=total_lines_inputs,
                                    outputs=y)

    # 5. Combine a token and char embedding into a hybrid embedding
    combined_embeddings = layers.Concatenate(name='tokne_char_hybrid_embedding')([token_model.output,
                                                                                char_model.output])
    z = layers.Dense(256, activation='relu')(combined_embeddings)
    z = layers.Dropout(0.5)(z)

    # 6. Combine positional embeddings with combined token and char embeddings into a tribrid embedding
    z = layers.Concatenate(name='token_char_positional_embedding')([line_number_model.output,
                                                                    total_line_model.output,
                                                                    z])

    # 7. Create output layer
    output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

    # 8. Put together model
    model_5 = tf.keras.Model(inputs=[line_number_model.input,
                                    total_line_model.input,
                                    token_model.input,
                                    char_model.input],
                            outputs=output_layer)
    
    # compile token, char, positional embedding model
    model_5.compile(loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.2), # add label smoothing (examples which are really confident get smoothed a little)
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    Same training setup as before, trained for 3 epochs, here are the validation metrics
    ```json
    {'accuracy': 83.27816761551702,
     'precision': 0.8317677427287499,
     'recall': 0.8327816761551702,
     'f1': 0.8319765983086386}
    ```

Naturally picked model 5 as my model to further train, here is the evaluation metrics on the test dataset (not seen by any of the models before)
```json
{'accuracy': 82.57176041148166,
 'precision': 0.8242659626849546,
 'recall': 0.8257176041148167,
 'f1': 0.8247141207593822}
```

When i went into development now, this became a huge problem for me.
First, i was not able to just load the model using a simple `tf.keras.load_model` since this is saved in the SavedModel format, a legacy format since Keras 3. I decided to make this work on keras 3 instead of keeping my dev env on keras 2. So i made a custom model loader to load the model
```py
class Keras2SavedModelWrapper(tf.keras.layers.Layer):
  """
  A custom layer to load a Keras 2 SavedModel and properly unpack
  dictionary inputs into the keyword arguments the graph expects.
  """
  def __init__(self, model_path, **kwargs):
    super().__init__(**kwargs)
    # load the raw saved model graph, explicitly placing on CPU
    with tf.device('/CPU:0'): # Ensure tf.saved_model.load happens on CPU
      self.loaded_model = tf.saved_model.load(model_path)
    self.serving_fn = self.loaded_model.signatures['serving_default']

  def call(self, inputs):
    # unpack the dictionary using ** so the graph
    # recives the exact keyword arguments it strictly requires.
    with tf.device('/CPU:0'): # Ensure the call operation also runs on CPU
      return self.serving_fn(**inputs)

def load_model(model_path):
  """
  Loads in a saved TensorFlow model from a specified path.
  """
  # defining identical input tensors with matching shapes, dtypes and names
  line_number_input = tf.keras.layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
  total_lines_input = tf.keras.layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
  token_inputs = tf.keras.layers.Input(shape=(), dtype=tf.string, name='token_inputs')
  char_inputs = tf.keras.layers.Input(shape=(1,), dtype=tf.string, name='char_inputs')

  # packaging my inputs into a directory matching my Keras 2 layer names
  # the tensorflow graph maps its execution endpoints via these names
  graph_inputs = {
      'line_number_input': line_number_input,
      'total_lines_input': total_lines_input,
      'token_inputs': token_inputs,
      'char_inputs': char_inputs
  }

  # loading the SavedModel directory as a functional block, ensuring all components are loaded to CPU
  with tf.device('/CPU:0'):
    tf_sm_layer = Keras2SavedModelWrapper(model_path)

  # extracting the output tensor from the graph by explicitly passing keyword arguments
  graph_outputs = tf_sm_layer(graph_inputs)

  final_predictions = graph_outputs['output_layer']

  # building the complete model
  model = tf.keras.Model(
      inputs=[line_number_input, total_lines_input, token_inputs, char_inputs],
      outputs=final_predictions
  )

  return model
```

This became my inference pipeline
```py
# Get a list of all physical GPUs
gpus = tf.config.list_physical_devices('GPU')

# If GPUs are available, disable them to force CPU usage
if gpus:
    try:
        tf.config.set_visible_devices([], 'GPU')
        logical_gpus = tf.config.list_logical_devices('GPU')
        print(f"Visible GPUs after disabling: {logical_gpus}")
    except RuntimeError as e:
        # Visible devices must be set at program startup
        print(e)
else:
    print("No GPU devices found, defaulting to CPU.")

loaded_model = load_model('/content/skimlit_tribrid_model')
```
Since, i knew i would not be able to deploy the complete project live for free, i decided to make a quick streamlit implementation for people to be able to test the model on the fly without needing to build the project on there local machine. Since streamlit community cloud only has 1GB ram (very generous btw!) There was no way my close to 1gb model would load and inference, infact it was consuming 3-4GB ram minimum in my github codespace env which only has a total of 7 something GB, with os packages, etc. i was getting OOM errors before the model even was loaded for inference, as this method was constructing two separated graphs initially. I knew this would not work, i need a magnitudes more efficient arhitecture on keras 3 that too, small enough to easily be hosted on community cloud's 1gb memory.

Keras_hub's all_minilm_l6_v2_en came to the rescue! a much lighter and substantially better architecure at just 80MB!

did 6 experiments with this architecure
1. Model 1
    architure,
    ```py
    # 1. Token inputs
    token_inputs = layers.Input(shape=(), dtype='string', name='token_inputs')

    # load the ultra-lightweight MiniLM TextEmbedder
    embedder = hub.models.TextEmbedder.from_preset(
        'all_minilm_l6_v2_en',
        trainable=False,
        name='token_embedder'
    )

    # freezing the embedder
    embedder.trainable = False

    preprocessed_tokens = embedder.preprocessor(token_inputs)

    # passing raw text through the embedder to get 384-dimensional vectors
    token_embeddings = embedder(preprocessed_tokens)

    # output dense layer, compressing the 384 dimensiosn down to 128 to get 384-dimensional vectors
    token_outputs = layers.Dense(128, activation='relu')(token_embeddings)

    token_model = tf.keras.Model(inputs=token_inputs,
                                outputs=token_outputs)

    # 2. Char inputs
    char_inputs = layers.Input(shape=(1,), dtype='string', name='char_inputs')
    char_vectors = char_vectorizer(char_inputs)
    char_embeddings = char_embed(char_vectors)
    char_bi_lstm = layers.Bidirectional(layers.LSTM(32))(char_embeddings)
    char_model = tf.keras.Model(inputs=char_inputs,
                                outputs=char_bi_lstm)

    # 3. Line numbers inputs
    line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
    x = layers.Dense(32, activation='relu')(line_number_inputs)
    line_number_model = tf.keras.Model(inputs=line_number_inputs,
                                    outputs=x)

    # 4. Total lines inputs
    total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
    y = layers.Dense(32, activation='relu')(total_lines_inputs)
    total_line_model = tf.keras.Model(inputs=total_lines_inputs,
                                    outputs=y)

    # 5. Combine a token and char embedding into a hybrid embedding
    combined_embeddings = layers.Concatenate(name='tokne_char_hybrid_embedding')([token_model.output,
                                                                                char_model.output])
    z = layers.Dense(256, activation='relu')(combined_embeddings)
    z = layers.Dropout(0.5)(z)

    # 6. Combine positional embeddings with combined token and char embeddings into a tribrid embedding
    z = layers.Concatenate(name='token_char_positional_embedding')([line_number_model.output,
                                                                    total_line_model.output,
                                                                    z])

    # 7. Create output layer
    output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

    # 8. Put together model
    model_1 = tf.keras.Model(inputs=[line_number_model.input,
                                    total_line_model.input,
                                    token_model.input,
                                    char_model.input],
                            outputs=output_layer)
    # compile token, char, positional embedding model
    model_1.compile(loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.2), # add label smoothing (examples which are really confident get smoothed a little)
                    optimizer='adam',
                    metrics=['accuracy'])
    ```
    trained for 5 epochs with the rest of the setup being same as before and here are the validation results
    `accuracy: 0.8362 - loss: 0.9314`

2. Model 2
    I thought initally that these scores are decent enough so decided to train the model from scratch on full dataset with the same training setup of 5 epochs, and these where the validation dataset results,
    `accuracy: 0.8647 - loss: 0.8849`

3. Model 3
    Same setup as model 2 but added early stopping callback and a reduce_lr callback
    ```py
    # early stopping callback
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=3,
        restore_best_weights=True # Always keeps the best epoch
    )

    # reduce_lr scheduler
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=2,
        min_lr=1e-6
    )

    # compile token, char, positional embedding model
    model_3.compile(loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.2), # add label smoothing (examples which are really confident get smoothed a little)
                    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0),
                    metrics=['accuracy'])
    ```
    Kept the max number of epochs to 25, model trained for a total of 20 epochs (10% data), and these are the validation set
    `accuracy: 0.8640 - loss: 0.8933
    
4. Model 4
    Now i explored fine-tuning the miniLM layer, so took model 3 and unfreezed the miniLM layer completely, trained using all the same callbacks, with a maximum of 25 epochs, it trained for 9 epochs. this is the validation score `accuracy: 0.8945 - loss: 0.8415`

5. Model 5
    Experimented with replacing the BiLSTM layer in character embeddings section with a Conv1D layer to see if i have any improvements, before finetuning on the complete data
    So, this was the model architecure
    ```py
    # 1. Token inputs
    token_inputs = layers.Input(shape=(), dtype='string', name='token_inputs')

    # load the ultra-lightweight MiniLM TextEmbedder
    embedder = hub.models.TextEmbedder.from_preset(
        'all_minilm_l6_v2_en',
        trainable=False,
        name='token_embedder'
    )

    # freezing the embedder
    embedder.trainable = False

    preprocessed_tokens = embedder.preprocessor(token_inputs)

    # passing raw text through the embedder to get 384-dimensional vectors
    token_embeddings = embedder(preprocessed_tokens)

    # output dense layer, compressing the 384 dimensiosn down to 128 to get 384-dimensional vectors
    token_outputs = layers.Dense(128, activation='relu')(token_embeddings)

    token_model = tf.keras.Model(inputs=token_inputs,
                                outputs=token_outputs)

    # 2. Char inputs
    char_inputs = layers.Input(shape=(1,), dtype='string', name='char_inputs')
    char_vectors = char_vectorizer(char_inputs)

    char_embed = layers.Embedding(
        input_dim=70,
        output_dim=25,
        name='embedding'
    )
    char_embeddings = char_embed(char_vectors)

    x = layers.Conv1D(
        filters=64,
        kernel_size=5,
        padding='same',
        activation='relu',
        name='char_conv1d'
    )(char_embeddings)

    char_conv_output = layers.GlobalMaxPooling1D(name='char_global_max_pooling')(x)

    char_model = tf.keras.Model(inputs=char_inputs,
                                outputs=char_conv_output,
                                name='char_model')

    # 3. Line numbers inputs
    line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
    x = layers.Dense(32, activation='relu')(line_number_inputs)
    line_number_model = tf.keras.Model(inputs=line_number_inputs,
                                    outputs=x)

    # 4. Total lines inputs
    total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
    y = layers.Dense(32, activation='relu')(total_lines_inputs)
    total_line_model = tf.keras.Model(inputs=total_lines_inputs,
                                    outputs=y)

    # 5. Combine a token and char embedding into a hybrid embedding
    combined_embeddings = layers.Concatenate(name='tokne_char_hybrid_embedding')([token_model.output,
                                                                                char_model.output])
    z = layers.Dense(256, activation='relu')(combined_embeddings)
    z = layers.Dropout(0.5)(z)

    # 6. Combine positional embeddings with combined token and char embeddings into a tribrid embedding
    z = layers.Concatenate(name='token_char_positional_embedding')([line_number_model.output,
                                                                    total_line_model.output,
                                                                    z])

    # 7. Create output layer
    output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

    # 8. Put together model
    model_5 = tf.keras.Model(inputs=[line_number_model.input,
                                    total_line_model.input,
                                    token_model.input,
                                    char_model.input],
                            outputs=output_layer)
    ```
    compiled and trained it with the same training setup, without any callbacks, for 3 epochs, for the feature extraction phase these are the validation results
    `0.8339 - loss: 0.9335`

    Then started fine tuning the model with unfrozen base with all the callbacks, trained for 9 epochs, this was the validation results
    accuracy: 0.8915 - loss: 0.8480`

6. Model 6
    Given the comparitvely poor performance with Conv1D layer instead of BiLSTM, i decided to fine tune the model on full dataset with the BiLSTM layer only, it took me 3.5 hours to train, ran out of google colab compute so had to restart the entire process with kaggle notebooks using their compute, and here are the final metrics on the test dataset
    ```json
    {'accuracy': 89.04264144682263,
     'precision': 0.8891034089368771,
     'recall': 0.8904264144682263,
     'f1': 0.8891953331713486}
    ```
    This is the model currently in final production code.

The model file size was 261MB, so i found a clever solution of stripping the optimization stages while loading the model so i would have a roughly 80 MB model in memory in server when loaded, to tackle the github file size limit of 100MB and to not push the 1GB ram of streamlit community cloud to its limits.

This is how i load my model in prod code
```py
def load_structura_model():
    """
    Extracts assets from the .keras archive, reconstructs the model architecture,
    and loads the trained weights directly from the internal .h5 file.
    """
    CURR_DIR = Path.cwd()
    keras_file_path = '/content/structura.keras'
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

    # 2. RECONSTRUCT TOKEN BRANCH (MINILM)
    token_inputs = layers.Input(shape=(), dtype=tf.string, name='token_inputs')

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

    # 3. RECONSTRUCT CHARACTER BRANCH
    char_inputs = layers.Input(shape=(1,), dtype=tf.string, name='char_inputs')

    with open(char_vocab_path, "r", encoding="utf-8") as f:
        char_vocab = [line.strip() for line in f if line.strip() and line.strip() != '[UNK]']

    char_vectorizer = layers.TextVectorization(
        name="text_vectorization",
        output_mode="int"
    )
    char_vectorizer.set_vocabulary(char_vocab)

    char_vectors = char_vectorizer(char_inputs)

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

    # 4. RECONSTRUCT POSITIONAL BRANCHES
    line_number_inputs = layers.Input(shape=(15,), dtype=tf.int32, name='line_number_input')
    x = layers.Dense(32, activation='relu', name='dense_1')(line_number_inputs)
    line_number_model = tf.keras.Model(inputs=line_number_inputs, outputs=x, name='line_number_model')

    total_lines_inputs = layers.Input(shape=(20,), dtype=tf.int32, name='total_lines_input')
    y = layers.Dense(32, activation='relu', name='dense_2')(total_lines_inputs)
    total_line_model = tf.keras.Model(inputs=total_lines_inputs, outputs=y, name='total_line_model')

    # 5. COMBINE BRANCHES & CLASSIFICATION HEAD
    combined_embeddings = layers.Concatenate(
        name='tokne_char_hybrid_embedding'
    )([token_model.output, char_model.output])

    z = layers.Dense(256, activation='relu', name='dense_3')(combined_embeddings)
    z = layers.Dropout(0.5, name='dropout')(z)

    z = layers.Concatenate(
        name='token_char_positional_embedding'
    )([line_number_model.output, total_line_model.output, z])

    output_layer = layers.Dense(5, activation='softmax', name='output_layer')(z)

    # 6. REASSEMBLE FULL MODEL
    model_2_reconstructed = tf.keras.Model(
        inputs=[
            line_number_model.input,
            total_line_model.input,
            token_model.input,
            char_model.input
        ],
        outputs=output_layer,
        name='model_4'
    )

    # 7. RESTORE TRAINED WEIGHTS
    model_2_reconstructed.load_weights(weights_path, skip_mismatch=True)

    return model_2_reconstructed
```

