

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
# %matplotlib inline

np.random.seed(2)

from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
import itertools
from tqdm import tqdm
import pytesseract
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPool2D
from tensorflow.keras.callbacks import ReduceLROnPlateau, EarlyStopping
from tensorflow.keras.optimizers import RMSprop
import os
import numpy as np
import cv2
from keras.models import load_model
from PIL import Image
from PIL import ImageChops, ImageEnhance
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from PIL import Image
from langdetect import detect
from datetime import datetime
import cv2

from langdetect import detect_langs  # For language detection
# Utility functions
import os

"""# Utility functions"""

def convert_to_ela_image(path, quality):
    filename = path
    resaved_filename = 'tempresaved.jpg'
    im = Image.open(filename)
    im.save(resaved_filename, 'JPEG', quality=quality)
    resaved_im = Image.open(resaved_filename)
    ela_im = ImageChops.difference(im, resaved_im)
    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)
    return ela_im

def is_image(file_path):
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    return any(file_path.lower().endswith(ext) for ext in image_extensions)


def build_image_list(path_to_data, label, images):
    for file in tqdm(os.listdir(path_to_data)):
        file_path = os.path.join(path_to_data, file)
        if is_image(file_path):
            images.append(file_path)
    return images

"""# Data Preparation

### Path to list of original and tampered documents specific to your needs
"""

custom_path_original = 'images/training/original'
custom_path_tampered = 'images/training/forged'

"""### Training dataset name"""

training_data_set = 'dataset.csv'

"""### Build image list for training"""

images = []
images = build_image_list(custom_path_original, '0', images)
images = build_image_list(custom_path_tampered, '1', images)

"""### Create a CSV file with image name (full path to image) and the label"""

image_name = []
label = []
language = []

for image_path in tqdm(images):
    image_name.append(image_path)
    label.append(os.path.basename(os.path.dirname(image_path)))  # Assuming folder name is the label
    try:
        # Extract text from image using OCR
        text = pytesseract.image_to_string(Image.open(image_path))
        # Detect language
        detected_lang = detect(text)
        language.append(detected_lang)
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        language.append('unknown')

dataset = pd.DataFrame({'image': image_name, 'class_label': label, 'language': language})
dataset.to_csv(training_data_set, index=False)

"""### Read the dataset and convert to ELA format for training"""

import numpy as np
from keras.utils import to_categorical
import pandas as pd

# Assuming convert_to_ela_image and other necessary functions are defined elsewhere

dataset = pd.read_csv('dataset.csv')
X = []
Y = []
for index, row in dataset.iterrows():
    print(f"Processing image: {row['image']}")  # Print the image path for debugging
    try:
        X.append(np.array(convert_to_ela_image(row['image'], 90).resize((128, 128))).flatten() / 255.0)
        Y.append(row['class_label'])
    except Exception as e:
        print(f"Error processing {row['image']}: {str(e)}")

X = np.array(X)
# Convert class labels to integers
class_labels = dataset['class_label'].astype('category').cat.codes
Y = to_categorical(class_labels, num_classes=2)
X = X.reshape(-1, 128, 128, 3)

"""### Train-Test split of the dataset"""

X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2, random_state=5)

"""# CNN Model"""

model = Sequential()

model.add(Conv2D(filters = 32, kernel_size = (3,3),padding = 'valid',
                activation ='relu', input_shape = (128,128,3)))
model.add(Conv2D(filters = 32, kernel_size = (3,3),padding = 'valid',
                activation ='relu'))
model.add(MaxPool2D(pool_size=(2,2)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(256, activation = "relu"))
model.add(Dropout(0.5))
model.add(Dense(2, activation = "softmax"))

model.summary()

"""# Model Training"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from tensorflow.keras.callbacks import ReduceLROnPlateau

# Define your model architecture
model = Sequential()

# Add convolutional layers
model.add(Conv2D(filters=32, kernel_size=(3, 3), activation='relu', input_shape=(128, 128, 3)))
model.add(Conv2D(filters=64, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(filters=128, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

# Flatten the feature maps to feed into a fully connected layer
model.add(Flatten())

# Add fully connected layers
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(2, activation='softmax'))  # 2 classes: Real and Fake

# Compile the model
optimizer = RMSprop(learning_rate=0.0005, rho=0.9, epsilon=1e-08, decay=0.0)
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

# Add learning rate reduction as callback
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=0.0001)

# Train the model
epochs = 50
batch_size = 50

history = model.fit(X_train, Y_train, batch_size=batch_size, epochs=epochs,
                    validation_data=(X_val, Y_val), callbacks=[reduce_lr], verbose=2)

"""# Save the model"""

import os
from datetime import datetime

models_dir = 'model'
current_time = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")  # Removed colon from format string
model_name = 'tampering_detection_' + current_time + '.keras'
model.save(os.path.join(models_dir, model_name))

models_artifact = '1.keras'  # Add the appropriate extension
model.save(os.path.join(models_dir, models_artifact))

"""# Model Performance

### Plot the loss and accuracy curves for training and validation
"""

fig, ax = plt.subplots(2, 1)

# Plotting training and validation loss
ax[0].plot(history.history['loss'], color='b', label="Training loss")
ax[0].plot(history.history['val_loss'], color='r', label="Validation loss")
legend = ax[0].legend(loc='best', shadow=True)

# Plotting training and validation accuracy
ax[1].plot(history.history['accuracy'], color='b', label="Training accuracy")
ax[1].plot(history.history['val_accuracy'], color='r', label="Validation accuracy")
legend = ax[1].legend(loc='best', shadow=True)

plt.show()

"""### Plot the confusion matrix"""

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')


# Predict the values from the validation dataset
Y_pred = model.predict(X_val)
# Convert predictions classes to one hot vectors
Y_pred_classes = np.argmax(Y_pred,axis = 1)
# Convert validation observations to one hot vectors
Y_true = np.argmax(Y_val,axis = 1)
# compute the confusion matrix
confusion_mtx = confusion_matrix(Y_true, Y_pred_classes)
# plot the confusion matrix
plot_confusion_matrix(confusion_mtx, classes = range(2))

"""### Evaluate"""

import cv2
import numpy as np

def evaluate_criteria(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate text density (percentage of white pixels in the image)
    total_pixels = gray_image.shape[0] * gray_image.shape[1]
    white_pixels = cv2.countNonZero(gray_image)
    text_density = white_pixels / total_pixels

    # Detect font changes
    # Placeholder logic: Check if there are multiple font types used in the document
    font_changes_detected = detect_font_changes(gray_image)

    # Detect color/texture changes
    # Placeholder logic: Check for significant changes in color or texture throughout the document
    color_texture_changes_detected = detect_color_texture_changes(image)

    # Evaluate based on the criteria
    if text_density < 0.7 or font_changes_detected or color_texture_changes_detected:
        return "Fake"
    else:
        return "Real"

def detect_font_changes(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image to obtain binary image
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours in the binary image
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Extract bounding rectangles for each contour
    bounding_rectangles = [cv2.boundingRect(contour) for contour in contours]

    # Sort bounding rectangles by x-coordinate to get left-to-right order
    bounding_rectangles.sort(key=lambda x: x[0])

    # Initialize a list to store the detected text areas
    text_areas = []

    # Iterate over bounding rectangles to extract text areas
    for x, y, w, h in bounding_rectangles:
        if w > 5 and h > 5:  # Filter out small noise contours
            text_areas.append(gray_image[y:y+h, x:x+w])

    # Placeholder logic to detect font changes
    # Check for differences in text sizes, font styles, etc.
    # For simplicity, we'll check if there are multiple text areas with varying sizes
    if len(text_areas) > 1:
        return True
    else:
        return False

def detect_color_texture_changes(image):
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Placeholder logic to detect color/texture changes
    # Calculate the standard deviation of pixel intensities
    std_dev = np.std(gray_image)

    # If the standard deviation is above a certain threshold, consider it a color/texture change
    # Adjust the threshold as needed based on your requirements
    if std_dev > 20:
        return True
    else:
        return False

import numpy as np

def add_noise(image, noise_level):
    # Add Gaussian noise
    noise = np.random.normal(loc=0, scale=noise_level, size=image.shape)
    noisy_image = np.clip(image + noise, 0, 255).astype(np.uint8)
    return noisy_image

model_path = "model/1.keras"
model = load_model(model_path)

import cv2
import numpy as np

def extract_features(image):
    # Initialize features dictionary
    features = {}

    # Calculate text density (percentage of white pixels in the image)
    total_pixels = image.shape[0] * image.shape[1]
    white_pixels = cv2.countNonZero(image)
    text_density = white_pixels / total_pixels
    features['text_density'] = text_density

    # Extract font information (e.g., font size, font style)
    # Implement font extraction logic here

    # Extract color/texture changes
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Compute Laplacian operator to detect edges
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
    # Calculate variance of Laplacian to measure texture changes
    texture_variation = np.var(laplacian)
    features['texture_variation'] = texture_variation

    # Implement additional feature extraction logic as needed

    return features

def preprocess_image(image_path, apply_noise=False, noise_level=25):
    # Load the image
    img = cv2.imread(image_path)
    # Convert to RGB format
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Resize the image to match the model's input shape
    img = cv2.resize(img, (128, 128))
    # Normalize the image
    img = img / 255.0
    # Add noise if specified
    if apply_noise:
        img = add_noise(img, noise_level)
    return img

def predict_image_authenticity(image_path):
    # Preprocess image
    img = preprocess_image(image_path)
    # Reshape for model input
    img = np.expand_dims(img, axis=0)
    # Predict
    prediction = model.predict(img)
    # Get predicted class
    predicted_class = np.argmax(prediction, axis=1)[0]
    return predicted_class

def predict_image_probabilities(image_path):
    # Preprocess image
    img = preprocess_image(image_path)
    # Reshape for model input
    img = np.expand_dims(img, axis=0)
    # Predict
    probabilities = model.predict(img)[0]
    return probabilities

images_folder = 'images/predict'
model_path = "model/1.keras"

model_path = "model/1.keras"
try:
    model = load_model(model_path)
except Exception as e:
    print("Error loading the model:", str(e))
    exit()

# Iterate through images and classify
for category in os.listdir(images_folder):
    category_path = os.path.join(images_folder, category)
    if os.path.isdir(category_path):
        for image_file in os.listdir(category_path):
            if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(category_path, image_file)
                try:
                    img = preprocess_image(image_path, apply_noise=True, noise_level=25)

                    # Reshape for model input
                    img = np.expand_dims(img, axis=0)
                    # Predict
                    probabilities = model.predict(img)[0]
                    authenticity = np.argmax(probabilities)
                    if category == "original" and authenticity == 0:
                        print(f"{image_file} is classified as REAL with probability: {probabilities[authenticity]}")
                    elif category == "tampered" and authenticity == 1:
                        print(f"{image_file} is classified as FAKE with probability: {probabilities[authenticity]}")
                    else:
                        print(f"{image_file} is classified incorrectly.")
                except Exception as e:
                    print(f"Error processing {image_file}: {str(e)}")
