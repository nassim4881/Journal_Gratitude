from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.data.tables import TableServiceClient
from config import TEXT_ANALYTICS_ENDPOINT, TEXT_ANALYTICS_KEY, STORAGE_CONNECTION_STRING, TABLE_NAME
import uuid
import random
import os

# Initialisation de Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modèle utilisateur
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, f"user{user_id}@example.com")

# Initialisation des services Azure
credential = AzureKeyCredential(TEXT_ANALYTICS_KEY)
text_analytics_client = TextAnalyticsClient(endpoint=TEXT_ANALYTICS_ENDPOINT, credential=credential)
table_service_client = TableServiceClient.from_connection_string(conn_str=STORAGE_CONNECTION_STRING)
table_client = table_service_client.get_table_client(TABLE_NAME)

# Citations inspirantes
POSITIVE_QUOTES = [
    "Continuez d'illuminer le monde avec votre positivité. 🌟",
    "Bravo, vous rayonnez de positivité aujourd'hui ! 😊",
    "Chaque sourire est une victoire. Bravo ! 🌈"
]
NEUTRAL_QUOTES = [
    "Chaque réflexion est une étape. Merci de partager vos pensées. 🌼",
    "Prenez un moment pour réfléchir à ce qui vous rend heureux. 🌞",
    "Ajoutez une entrée positive pour illuminer votre journée ! ✨"
]
NEGATIVE_QUOTES = [
    "Courage, exprimer vos émotions est une première étape vers le mieux-être. 🤗",
    "Après la pluie vient le beau temps. 🌈",
    "Prenez soin de vous, chaque jour compte. 🌟"
]
WELCOME_MESSAGES = [
    "Heureux de vous revoir, {pseudo}. Continuez votre parcours de gratitude. 😊",
    "Bienvenue à nouveau, {pseudo}. Partagez votre gratitude pour illuminer votre journée ! 🌟",
    "Content de vous retrouver, {pseudo}. Continuons ce beau voyage ensemble ! 🌈"
]

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')  # Champ pour le mot de passe
        
        # Vérifier le mot de passe si c'est l'admin
        if email.lower() == "admin" and password == "admin123":
            user_id = email.split('@')[0]
            user = User(id=user_id, email=email)
            login_user(user)
            return redirect(url_for('show_entries', reconnected=True))
        
        # Vérification standard pour les autres utilisateurs
        user_id = email.split('@')[0]
        user = User(id=user_id, email=email)
        login_user(user)
        return redirect(url_for('show_entries', reconnected=True))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def show_entries():
    try:
        entities = table_client.query_entities("PartitionKey eq 'GratitudeJournal'")
    except Exception as e:
        return f"Erreur de récupération des données: {str(e)}", 500

    entries = []
    positive_count = 0
    neutral_count = 0
    negative_count = 0

    for entity in entities:
        entries.append({
            "Text": entity.get("Text"),
            "Sentiment": entity.get("Sentiment"),
            "PositiveScore": entity.get("PositiveScore"),
            "NeutralScore": entity.get("NeutralScore"),
            "NegativeScore": entity.get("NegativeScore"),
            "RowKey": entity.get("RowKey"),
            "UserID": entity.get("UserID")
        })

        # Comptabilise les statistiques
        if entity.get("Sentiment") == "positive":
            positive_count += 1
        elif entity.get("Sentiment") == "neutral":
            neutral_count += 1
        elif entity.get("Sentiment") == "negative":
            negative_count += 1

    # Détermine le message selon le contexte
    if request.args.get('reconnected'):
        message = random.choice(WELCOME_MESSAGES).format(pseudo=current_user.id.upper())
    elif request.args.get('last_sentiment') == 'positive':
        message = random.choice(POSITIVE_QUOTES)
    elif request.args.get('last_sentiment') == 'neutral':
        message = random.choice(NEUTRAL_QUOTES)
    elif request.args.get('last_sentiment') == 'negative':
        message = random.choice(NEGATIVE_QUOTES)
    else:
        message = None

    return render_template(
        'index.html',
        entries=entries,
        current_user_id=current_user.id,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        message=message
    )

@app.route('/add-entry', methods=['GET'])
@login_required
def add_entry_form():
    return render_template('add_entry.html')

@app.route('/submit-entry', methods=['POST'])
@login_required
def submit_entry_form():
    text = request.form.get('text')
    if not text:
        return "Texte requis", 400

    documents = [text]
    try:
        response = text_analytics_client.analyze_sentiment(documents=documents)[0]
    except Exception as e:
        return f"Erreur d'analyse de sentiment: {str(e)}", 500

    row_key = str(uuid.uuid4())
    entry = {
        "PartitionKey": "GratitudeJournal",
        "RowKey": row_key,
        "Text": text,
        "Sentiment": response.sentiment,
        "PositiveScore": response.confidence_scores.positive,
        "NeutralScore": response.confidence_scores.neutral,
        "NegativeScore": response.confidence_scores.negative,
        "UserID": current_user.id
    }
    try:
        table_client.create_entity(entity=entry)
    except Exception as e:
        return f"Erreur d'ajout de l'entrée: {str(e)}", 500

    return redirect(url_for('show_entries', last_sentiment=response.sentiment))

@app.route('/edit-entry/<row_key>', methods=['GET'])
@login_required
def edit_entry(row_key):
    try:
        entity = table_client.get_entity(partition_key="GratitudeJournal", row_key=row_key)
    except Exception as e:
        return f"Erreur de récupération de l'entrée: {str(e)}", 500

    if entity.get("UserID") == current_user.id or current_user.id.lower() == "admin":  # Admin peut aussi modifier
        return render_template('edit_entry.html', entry=entity)
    return "Action non autorisée", 403

@app.route('/delete-entry/<row_key>', methods=['GET'])
@login_required
def delete_entry(row_key):
    try:
        entity = table_client.get_entity(partition_key="GratitudeJournal", row_key=row_key)
        if entity.get("UserID") == current_user.id or current_user.id.lower() == "admin":  # Admin peut aussi supprimer
            table_client.delete_entity(partition_key="GratitudeJournal", row_key=row_key)
            return redirect(url_for('show_entries'))
    except Exception as e:
        return f"Erreur lors de la suppression: {str(e)}", 500
    return "Action non autorisée", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
