# Impor library standar
import json
import os
import datetime
import random
import logging

# Impor library untuk matematika dan data handling
import numpy as np

# Impor library Flask untuk web server
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache

# Impor library NLTK untuk pemrosesan teks
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.translate.bleu_score import sentence_bleu
from nltk.corpus import wordnet

# Impor library sklearn untuk feature extraction dan cosine similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Impor library untuk deteksi bahasa dan penilaian ROUGE
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from rouge import Rouge

app = Flask(__name__)

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konfigurasi cache
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

class ConversationManager:
    def __init__(self, filepath="data/data.json"):
        self.filepath = filepath
        self.data = self.load_data()
        self.vectorizer = TfidfVectorizer()
        self.train_vectorizer()

    def load_data(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as file:
                return json.load(file)
        else:
            data = {"conversations": []}
            self.save_data(data)
            return data

    def save_data(self):
        with open(self.filepath, "w") as file:
            json.dump(self.data, file, indent=4)

    def update_conversation(self, question, new_answer, new_feedback):
        found = False
        for conv in self.data['conversations']:
            if conv['question'] == question:
                conv['answer'] = new_answer
                conv['feedback'] = new_feedback
                found = True
                break
        if not found:
            timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
            self.data['conversations'].append({'question': question, 'answer': new_answer, 'timestamp': timestamp, 'feedback': new_feedback, 'language': detect(question)})
        self.save_data()
        self.train_vectorizer()

    def train_vectorizer(self):
        if self.data["conversations"]:
            all_texts = [conv["question"] for conv in self.data["conversations"]]
            self.vectorizer.fit(all_texts)

    def add_conversation(self, question, answer, language):
        timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
        self.data["conversations"].append({"question": question, "answer": answer, "timestamp": timestamp, "language": language, "feedback": ""})
        self.save_data()
        self.train_vectorizer()

conv_manager = ConversationManager()

@cache.memoize(60)
def preprocess(text, language='en'):
    try:
        stop_words = set(stopwords.words(language))
    except OSError:
        stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(text.lower())
    filtered_words = [lemmatizer.lemmatize(word) for word in words if word.isalnum() and not word in stop_words]
    return " ".join(filtered_words)

def generate_response_from_context(question, language='en'):
    stop_words = set(stopwords.words(language))
    lemmatizer = WordNetLemmatizer()

    # Tokenisasi dan lemmatisasi pertanyaan
    words = [lemmatizer.lemmatize(word) for word in word_tokenize(question.lower()) if word.isalnum() and word not in stop_words]

    relevant_responses = []

    # Cari kalimat dalam data yang memiliki kata kunci yang banyak sama
    for conv in conv_manager.data['conversations']:
        conv_words = set([lemmatizer.lemmatize(word) for word in word_tokenize(conv['question'].lower()) if word.isalnum() and word not in stop_words])
        common_words = conv_words.intersection(words)

        if common_words:
            score = len(common_words)
            relevant_responses.append((score, conv['answer'], conv['question']))

    if not relevant_responses:
        return None

    # Urutkan berdasarkan skor kesamaan dan ambil jawaban dengan skor tertinggi
    relevant_responses.sort(reverse=True, key=lambda x: x[0])
    best_response = relevant_responses[0][1]
    best_question = relevant_responses[0][2]

    # Membuat kalimat baru berdasarkan struktur kalimat pertanyaan dan jawaban terbaik
    new_response = reconstruct_response(best_response, question, best_question, words)
    return new_response

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return synonyms

def reconstruct_response(best_response, user_question, best_matched_question):
    tokenized_best_response = word_tokenize(best_response.lower())
    tokenized_user_question = word_tokenize(user_question.lower())
    tokenized_best_matched_question = word_tokenize(best_matched_question.lower())

    # Buat kamus sinonim untuk kata-kata dalam pertanyaan terbaik
    synonyms_map = {word: get_synonyms(word) for word in tokenized_best_matched_question}

    # Cari kata terdekat dalam pertanyaan pengguna untuk setiap kata dalam jawaban
    new_response = []
    for word in tokenized_best_response:
        if word in synonyms_map:
            # Cari kata terbaik yang bisa menggantikan berdasarkan sinonimnya
            best_match = None
            for synonym in synonyms_map[word]:
                if synonym in tokenized_user_question:
                    best_match = synonym
                    break
            new_response.append(best_match if best_match else word)
        else:
            new_response.append(word)

    # Gabungkan kembali menjadi kalimat
    return ' '.join(new_response)

def get_response(user_input):
    try:
        language = detect(user_input)
    except LangDetectException:
        language = "en"

    processed_input = preprocess(user_input, language)
    if not conv_manager.data["conversations"]:
        return "Belum ada data yang cukup."

    vectors = conv_manager.vectorizer.transform([processed_input])
    existing_questions = [preprocess(conv["question"], language) for conv in conv_manager.data["conversations"]]
    question_vectors = conv_manager.vectorizer.transform(existing_questions)
    similarity = cosine_similarity(vectors, question_vectors)

    max_sim = max(similarity[0])
    if max_sim > 0.4:
        index = np.argmax(similarity)
        return conv_manager.data["conversations"][index]["answer"]
    else:
        new_response = generate_response_from_context(user_input, language)
        if new_response:
            return new_response
        else:
            placeholder_answer = f"Saya tidak yakin dengan jawaban pasti untuk '{user_input}', tapi saya akan mencoba belajar lebih banyak tentang topik ini."
            conv_manager.add_conversation(user_input, placeholder_answer, language)
            return placeholder_answer

def calculate_bleu(reference, candidate):
    return sentence_bleu([reference.split()], candidate.split())

def calculate_rouge(reference, candidate):
    rouge = Rouge()
    scores = rouge.get_scores(candidate, reference)
    return scores[0]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = data.get("user_input", "").strip()
    if not user_input:
        logging.error("No input provided by the user.")
        return jsonify({"error": "No input provided"}), 400
    
    # Tambahkan log untuk melihat input pengguna
    logging.info(f"Received user input: {user_input}")

    if len(user_input) < 1 or len(user_input) > 2000:
        logging.error("Invalid input length.")
        return jsonify({"error": "Input is too long or too short"}), 400

    try:
        response = get_response(user_input)
        conv_manager.add_conversation(user_input, response, detect(user_input))
        # Log the generated response
        logging.info(f"Generated response: {response}")
        return jsonify({"response": response, "language": detect(user_input)}), 200
    except Exception as e:
        logging.error(f"Error in processing the user input: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    user_question = data.get("question")
    user_feedback = data.get("feedback")
    if not user_question or not user_feedback:
        return jsonify({"error": "Question and feedback must be provided"}), 400

    conv_manager.update_conversation(user_question, "", user_feedback)
    return jsonify({"message": "Feedback received and conversation updated. Thank you!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
