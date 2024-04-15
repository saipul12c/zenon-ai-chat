# Impor library standar
import json
import os
import datetime
import random
import logging
import nltk

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
from translate import Translator

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
        self.update_count = 0
        self.update_threshold = 10  # Melakukan retrain setiap ada 10 perubahan

    def load_data(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as file:
                return json.load(file)
        else:
            data = {"conversations": []}
            self.save_data(data)
            return data

    def save_data(self, data=None):
        if data is None:
            data = self.data
        with open(self.filepath, "w") as file:
            json.dump(data, file, indent=4)

    def update_conversation(self, question, new_answer, new_feedback):
        if not new_answer.strip() or not new_feedback.strip():
            return "Jawaban dan umpan balik tidak boleh kosong."

        found = False
        language = detect(question)  # Mendeteksi bahasa dari pertanyaan yang diberikan
        for conv in self.data['conversations']:
            if conv['question'] == question:
                conv['answer'] = new_answer
                conv['feedback'] = new_feedback
                conv['language'] = language  # Memperbarui bahasa juga
                found = True
                break
        if not found:
            timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
            self.data['conversations'].append({
                'question': question,
                'answer': new_answer,
                'timestamp': timestamp,
                'feedback': new_feedback,
                'language': language  # Memastikan bahasa disertakan saat menambahkan baru
            })

            self.save_data()
            self.update_count += 1
            if self.update_count >= self.update_threshold:
                self.train_vectorizer()
                self.update_count = 0

            return "Data berhasil diperbarui."

    def train_vectorizer(self):
        if self.data["conversations"]:
            all_texts = [conv["question"] for conv in self.data["conversations"]]
            self.vectorizer.fit(all_texts)

    def add_conversation(self, question, answer, language):
        timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
        self.data["conversations"].append({"question": question, "answer": answer, "timestamp": timestamp, "language": language, "feedback": ""})
        self.save_data()
        self.update_count += 1
        if self.update_count >= self.update_threshold:
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
    lemmatizer = WordNetLemmatizer()
    
    # Menentukan stopwords berdasarkan bahasa input jika tersedia, jika tidak, gunakan bahasa Inggris
    try:
        stop_words = set(stopwords.words(language))
    except:
        stop_words = set(stopwords.words('english'))
    
    # Tokenisasi dan lemmatisasi pertanyaan dengan stopwords
    words = [lemmatizer.lemmatize(word) for word in word_tokenize(question.lower()) if word.isalnum() and word not in stop_words]
    relevant_responses = []

    # Cari kalimat dalam data yang memiliki kata kunci yang banyak sama
    for conv in conv_manager.data['conversations']:
        conv_stop_words = set(stopwords.words('english'))
        conv_words = set([lemmatizer.lemmatize(word) for word in word_tokenize(conv['question'].lower()) if word.isalnum() and word not in conv_stop_words])
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

    # Jika bahasa pengguna bukan 'en', terjemahkan jawaban ke dalam bahasa target
    if language != 'en':
        translator = Translator(to_lang=language)
        best_response = translator.translate(best_response)

    # Membuat kalimat baru berdasarkan struktur kalimat pertanyaan dan jawaban terbaik
    return reconstruct_response(best_response, question, best_question)

def get_synonyms(word, pos=None):
    lemmatizer = WordNetLemmatizer()
    word = lemmatizer.lemmatize(word)
    
    synonyms = set()
    for syn in wordnet.synsets(word, pos=pos if pos else None):
        for lemma in syn.lemmas():
            normalized_lemma = lemma.name().replace('_', ' ').lower()
            synonyms.add(normalized_lemma)
    return synonyms

def reconstruct_response(best_response, user_question, best_matched_question):
    tokenized_best_response = word_tokenize(best_response.lower())
    tokenized_user_question = word_tokenize(user_question.lower())
    tokenized_best_matched_question = word_tokenize(best_matched_question.lower())
    synonyms_map = {word: get_synonyms(word) for word in tokenized_best_matched_question}
    new_response = []

    for word in tokenized_best_response:
        if word in synonyms_map:
            best_match = None
            for synonym in synonyms_map[word]:
                if synonym in tokenized_user_question:
                    best_match = synonym
                    break
            new_response.append(best_match if best_match else word)
        else:
            new_response.append(word)

    return ' '.join(new_response)
    
def get_response(user_input):
    try:
        language = detect(user_input)
    except LangDetectException:
        language = "en"  # Gunakan Bahasa Inggris sebagai default jika deteksi gagal

    processed_input = preprocess(user_input, language)
    if not conv_manager.data["conversations"]:
        return "Belum ada data yang cukup."

    vectors = conv_manager.vectorizer.transform([processed_input])
    existing_questions = [preprocess(conv["question"], conv['language']) for conv in conv_manager.data["conversations"]]  # Gunakan bahasa dari masing-masing pertanyaan yang tersimpan
    question_vectors = conv_manager.vectorizer.transform(existing_questions)
    similarity = cosine_similarity(vectors, question_vectors)

    max_sim = max(similarity[0])
    if max_sim > 0.4:  # Pertimbangkan untuk menyesuaikan threshold ini berdasarkan analisis lebih lanjut
        index = np.argmax(similarity)
        best_match = conv_manager.data["conversations"][index]
        additional_info = f"Jawaban ini didasarkan pada pertanyaan serupa: '{best_match['question']}'"
        return f"{best_match['answer']} (Info: {additional_info})"
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

@app.route('/help-faq')
def help_faq():
    return render_template('faq/help_faq.html')

@app.route('/release-note')
def release_note():
    return render_template('note/release_note.html')

@app.route('/terms-policies')
def terms_policies():
    return render_template('polices/terms_policies.html')

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = data.get("user_input", "").strip()
    if not user_input:
        logging.error("No input provided by the user.")
        return jsonify({"error": "No input provided"}), 400
    
    logging.info(f"Received user input: {user_input}")

    if len(user_input) > 2000:
        logging.error("Invalid input length.")
        return jsonify({"error": "Input is too long"}), 400

    try:
        response = get_response(user_input)
        language = detect(user_input)
        conv_manager.add_conversation(user_input, response, language)

        # Evaluasi respon jika memungkinkan
        possible_matches = [conv for conv in conv_manager.data["conversations"] if conv["question"] == user_input]
        if possible_matches:
            reference_response = possible_matches[0]['answer']
            # Hanya hitung skor jika ada perubahan jawaban
            if 'last_updated' not in possible_matches[0] or (datetime.datetime.utcnow() - possible_matches[0]['last_updated']).total_seconds() > 3600:
                bleu_score = calculate_bleu(reference_response, response)
                rouge_score = calculate_rouge(reference_response, response)
                possible_matches[0]['last_updated'] = datetime.datetime.utcnow()
                logging.info(f"Evaluation - BLEU: {bleu_score}, ROUGE: {rouge_score['rouge-l']['f']}")
            else:
                bleu_score = rouge_score = "N/A"

            return jsonify({"response": response, "language": language, "BLEU": bleu_score, "ROUGE": rouge_score}), 200
        return jsonify({"response": response, "language": language}), 200
    except Exception as e:
        logging.error(f"Error in processing the user input: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    user_question = data.get("question", "").strip()
    user_feedback = data.get("feedback", "").strip()

    if not user_question or not user_feedback:
        return jsonify({"error": "Both question and feedback must be provided and cannot be empty"}), 400

    # Update conversation with new feedback and recalculate BLEU/ROUGE scores
    conv_manager.update_conversation(user_question, "", user_feedback)
    all_conv = [conv for conv in conv_manager.data["conversations"] if conv["question"] == user_question]
    if all_conv:
        updated_response = all_conv[0]["answer"]
        new_bleu_score = calculate_bleu(updated_response, user_feedback)
        new_rouge_score = calculate_rouge(updated_response, user_feedback)
        logging.info(f"Updated Evaluation - BLEU: {new_bleu_score}, ROUGE: {new_rouge_score['rouge-l']['f']}")

        return jsonify({
            "message": "Feedback received and conversation updated. Thank you!",
            "BLEU": new_bleu_score,
            "ROUGE": new_rouge_score
        }), 200
    else:
        return jsonify({"error": "No matching question found in the database."}), 404

if __name__ == "__main__":
    app.run(debug=True)
