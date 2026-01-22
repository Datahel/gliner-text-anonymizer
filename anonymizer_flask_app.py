from flask import Flask, render_template, request, session, send_file
from flask_session import Session
import pandas as pd
from text_anonymizer import TextAnonymizer
from text_anonymizer.config_cache import ConfigCache
from werkzeug.utils import secure_filename
import io
import os
import logging
import secrets

logging.getLogger().setLevel(logging.WARN)

app = Flask(__name__, template_folder='flask/templates', static_folder='flask/static')
app.logger.setLevel(logging.INFO)

if not os.getenv("SECRET_KEY"):
    secret_key = secrets.token_hex(32)
    app.logger.warning(f"No SECRET_KEY set. Generated temporary key: {secret_key}")
    app.logger.warning("Set this as an environment variable for consistency across restarts.")
    app.secret_key = secret_key
else:
    app.secret_key = os.getenv("SECRET_KEY")

app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
Session(app)

app.config['UPLOAD_FOLDER'] = 'uploads'  # Define a folder to store uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size, here set to 16MB

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Init anonymizer as singleton
text_anonymizer = TextAnonymizer(languages=['fi', 'en'], debug_mode=False)

# Load label mappings from config first
config_cache = ConfigCache.instance()
label_mappings = config_cache.get_label_mappings()


def get_label_display_name(label: str) -> str:
    """
    Get display name for a label using label_mappings.

    Examples:
        'person_ner' -> removes '_ner', converts to 'PERSON' -> maps to 'NIMI'
        'fi_hetu_regex' -> removes '_regex', converts to 'FI_HETU' -> maps to 'HETU'
    """
    if label.endswith('_ner'):
        # NER label: remove suffix and convert to uppercase
        key = label[:-4].upper()
    elif label.endswith('_regex'):
        # Regex label: remove suffix and convert to uppercase
        key = label[:-6].upper()
    else:
        # Fallback
        key = label.upper()

    # Look up in mappings, fallback to key itself
    return label_mappings.get(key, key)


# Available labels for the UI (grouped by type) - now with display names
NER_LABELS = [
    ('person_ner', get_label_display_name('person_ner')),
    ('email_ner', get_label_display_name('email_ner')),
    ('phone_number_ner', get_label_display_name('phone_number_ner')),
    ('address_ner', get_label_display_name('address_ner')),
    ('organization_ner', get_label_display_name('organization_ner')),
    ('location_ner', get_label_display_name('location_ner')),
]

REGEX_LABELS = [
    ('fi_hetu_regex', get_label_display_name('fi_hetu_regex')),
    ('fi_puhelin_regex', get_label_display_name('fi_puhelin_regex')),
    ('fi_rekisteri_regex', get_label_display_name('fi_rekisteri_regex')),
    ('fi_iban_regex', get_label_display_name('fi_iban_regex')),
]

ALL_LABELS = NER_LABELS + REGEX_LABELS

# Default threshold
DEFAULT_THRESHOLD = 0.6


@app.route("/", methods=["GET"])
def index():
    # Pääsivu, jossa on linkit tai napit, jotka ohjaavat käyttäjän oikeaan lomakkeeseen
    return render_template("index.html")

@app.route("/plain_text", methods=["GET", "POST"])
def plain_text():
    if request.method == "POST":
        return handle_text_anonymization(request)
    else:
        return render_template("plain_text.html",
                               ner_labels=NER_LABELS,
                               regex_labels=REGEX_LABELS,
                               default_threshold=DEFAULT_THRESHOLD)

@app.route("/text_file", methods=["GET", "POST"])
def text_file():
    if request.method == "POST":
        if "file" in request.files:
            return handle_text_file_anonymization(request)
    return render_template("text_file.html",
                           ner_labels=NER_LABELS,
                           regex_labels=REGEX_LABELS,
                           default_threshold=DEFAULT_THRESHOLD)

@app.route("/csv", methods=["GET", "POST"])
def csv():
    if request.method == "POST":
        if "file" in request.files:
            return handle_csv_upload(request)
        else:
            return handle_csv_anonymization(request)
    else:
        return render_template("csv.html",
                               ner_labels=NER_LABELS,
                               regex_labels=REGEX_LABELS,
                               default_threshold=DEFAULT_THRESHOLD,
                               phase="upload")

def handle_csv_upload(request):
    
    uploaded_file = None
    if 'file' in request.files:
        uploaded_file = request.files['file']
    # Handle uploaded file
    
    # Check if there is a file and it has a CSV filename
    if uploaded_file and uploaded_file.filename.endswith('.csv'):
        try:
            separator = request.form.get('separator', ',')
            encoding = request.form.get('encoding', 'utf-8')
            filename = secure_filename(uploaded_file.filename)

            # Read the contents of the file into a DataFrame without saving it to disk
            file_stream = io.StringIO(uploaded_file.stream.read().decode(encoding), newline=None)
            dataframe = pd.read_csv(file_stream, sep=separator, dtype=str, encoding=encoding, index_col=False)

            # Store the DataFrame in the session after converting it to JSON
            session['dataframe'] = dataframe.to_json(orient='split', date_format='iso')
            session['filename'] = filename
            columns = dataframe.columns.tolist()

            return render_template('csv.html',
                                   columns=columns,
                                   ner_labels=NER_LABELS,
                                   regex_labels=REGEX_LABELS,
                                   default_threshold=DEFAULT_THRESHOLD,
                                   phase="column_selection")
        except Exception as e:
            app.logger.exception('Csv upload failed: %s', str(e))

    return render_template("csv.html",
                           error="Tiedoston lukeminen ei onnistunut. Tarkista erotinmerkki ja merkistö.",
                           phase="upload")

def handle_csv_anonymization(request):
    # If no columns selected, return to page with column selection
    column_selection = None
    if request.form:
        column_selection = request.form.getlist('columns')

    
    if not column_selection or len(column_selection) == 0:
        
        if 'dataframe' in session:
            app.logger.info("Dataframe not in session. Forward to column selection page.")
            dataframe_json = session['dataframe']
            dataframe = pd.read_json(dataframe_json, orient='split')
            columns = dataframe.columns.tolist()
            
            return render_template('csv.html',
                                   columns=columns,
                                   error="Valitse sarakkeet, jotka haluat anonymisoida.",
                                   ner_labels=NER_LABELS,
                                   regex_labels=REGEX_LABELS,
                                   default_threshold=DEFAULT_THRESHOLD,
                                   phase="column_selection")
        else:
            # Return an error message or redirect if there is no dataframe in the session
            return render_template("csv.html", error="Sessio on vanhentunut.",
                                   phase="upload")

    else:
        # If columns selected and data is in session, anonymize them and return the anonymized file
        if 'dataframe' in session:
            app.logger.info("Dataframe found in session. Anonymizing...")
            try:
                # Get labels from form (new API)
                labels = request.form.getlist('labels')
                if not labels:
                    labels = None  # Use defaults

                # Get threshold
                try:
                    gliner_threshold = float(request.form.get('gliner_threshold', DEFAULT_THRESHOLD))
                except (ValueError, TypeError):
                    gliner_threshold = DEFAULT_THRESHOLD

                dataframe_json = session['dataframe']
                dataframe = pd.read_json(io.StringIO(dataframe_json), orient='split')
                encoding = request.form.get('encoding', 'utf-8')

                app.logger.info(f"CSV anonymization: labels={labels}, threshold={gliner_threshold}")

                # Anonymize selected columns
                for column in column_selection:
                    app.logger.info(f"Anonymizing column {column}")
                    dataframe[column] = dataframe[column].apply(
                        lambda x: text_anonymizer.anonymize(
                            x,
                            labels=labels,
                            gliner_threshold=gliner_threshold
                        ).anonymized_text
                    )

                resp = io.StringIO()
                dataframe.to_csv(resp, encoding=encoding, index=False)
                resp.seek(0)

                # add _anonymized to original filename
                filename = secure_filename(session['filename'])
                filename = filename.replace('.csv', '_anonymized.csv')
                app.logger.info("Anonymization done. Returning anonymized csv.")

                return send_file(
                    io.BytesIO(resp.getvalue().encode(encoding)),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            except Exception as e:
                app.logger.exception('Csv anonymization failed with exception: %s', str(e))
                return render_template("csv.html", error="Tiedoston anonymisointi ei onnistunut.",
                                       phase="upload")
        else:
            return render_template("csv.html", error="Ei tiedostoa",
                                  phase="upload")

def handle_text_file_anonymization(request):
    uploaded_file = None
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename.endswith('.txt'):
            try:
                encoding = request.form.get('encoding', 'utf-8')
                input_text = uploaded_file.stream.read().decode(encoding)

                # Get labels from form (new API)
                labels = request.form.getlist('labels')
                if not labels:
                    labels = None  # Use defaults

                # Get threshold
                try:
                    gliner_threshold = float(request.form.get('gliner_threshold', DEFAULT_THRESHOLD))
                except (ValueError, TypeError):
                    gliner_threshold = DEFAULT_THRESHOLD

                app.logger.info(f"Text file anonymization: labels={labels}, threshold={gliner_threshold}")

                anonymized_str = text_anonymizer.anonymize(
                    input_text,
                    labels=labels,
                    gliner_threshold=gliner_threshold
                ).anonymized_text

                # add _anonymized to original filename
                filename = secure_filename(uploaded_file.filename)
                filename = filename.replace('.txt', '_anonymized.txt')

                return send_file(
                    io.BytesIO(anonymized_str.encode(encoding)),
                    mimetype='plain/text',
                    as_attachment=True,
                    download_name=filename
                )

            except Exception as e:
                app.logger.exception('Error handling txt file: %s', str(e))
                return render_template("text_file.html",
                                       ner_labels=NER_LABELS,
                                       regex_labels=REGEX_LABELS,
                                       default_threshold=DEFAULT_THRESHOLD,
                                       error="Tiedoston anonymisointi ei onnistunut. Tarkista onko merkistö oikein.")

    return render_template("text_file.html",
                           ner_labels=NER_LABELS,
                           regex_labels=REGEX_LABELS,
                           default_threshold=DEFAULT_THRESHOLD)


def handle_text_anonymization(request):
    text = request.form['text']

    # Get labels from form (new API)
    labels = request.form.getlist('labels')
    if not labels:
        labels = None  # Use defaults

    # Get threshold
    try:
        gliner_threshold = float(request.form.get('gliner_threshold', DEFAULT_THRESHOLD))
    except (ValueError, TypeError):
        gliner_threshold = DEFAULT_THRESHOLD

    app.logger.info(f"Text anonymization: labels={labels}, threshold={gliner_threshold}")

    anonymized_text = text_anonymizer.anonymize(
        text,
        labels=labels,
        gliner_threshold=gliner_threshold
    ).anonymized_text.strip()

    return render_template("plain_text.html",
                           anonymized_text=anonymized_text,
                           ner_labels=NER_LABELS,
                           regex_labels=REGEX_LABELS,
                           default_threshold=DEFAULT_THRESHOLD,
                           text=text)


if __name__ == "__main__":

    app.run(debug=False)