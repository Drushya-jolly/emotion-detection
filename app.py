from flask import Flask, redirect, render_template, request, url_for
from deepface import DeepFace
import os
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("static", "uploads")  # static/uploads/
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if request.method == 'POST':
        entry = request.form.get('journalText', '').strip()
        if entry:
            with open('journal.txt', 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp}\n{entry}\n---\n")

    journal_entries = []
    if os.path.exists('journal.txt'):
        with open('journal.txt', 'r', encoding='utf-8') as f:
            raw_entries = f.read().strip().split('---\n')
            for entry in raw_entries:
                if entry.strip():
                    # split timestamp and content by first newline
                    parts = entry.strip().split('\n', 1)
                    if len(parts) == 2:
                        journal_entries.append({'timestamp': parts[0], 'content': parts[1]})
    # Show newest first
    journal_entries.reverse()

    return render_template('journal.html', journal=journal_entries)

@app.route('/delete_entry', methods=['POST'])
def delete_entry():
    timestamp = request.form.get('timestamp')
    if timestamp and os.path.exists('journal.txt'):
        with open('journal.txt', 'r', encoding='utf-8') as f:
            entries = f.read().strip().split('---\n')
        entries = [e for e in entries if not e.startswith(timestamp)]
        with open('journal.txt', 'w', encoding='utf-8') as f:
            for e in entries:
                f.write(e.strip() + '\n---\n')
    return redirect(url_for('journal'))

@app.route('/mood')
def mood():
    return render_template("index.html")

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'photo' not in request.files:
        return render_template('index.html', error="No file part")

    file = request.files['photo']

    if file.filename == '':
        return render_template('index.html', error="No selected file")

    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d%H%M%S") + os.path.splitext(file.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            result = DeepFace.analyze(img_path=filepath, actions=['emotion'])
            emotion = result[0]['dominant_emotion']
        except Exception as e:
            return render_template('index.html', error="Error analyzing emotion.")

        image_url = url_for('static', filename=f'uploads/{filename}')
        return render_template('index.html', emotion=emotion, image_url=image_url)

    else:
        return render_template('index.html', error="Invalid file format")

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    todos = []
    if os.path.exists('todo.txt'):
        with open('todo.txt', 'r', encoding='utf-8') as f:
            todos = [line.strip() for line in f if line.strip()]

    if request.method == 'POST':
        task = request.form.get('task', '').strip()
        if task:
            with open('todo.txt', 'a', encoding='utf-8') as f:
                f.write(f"{task}\n")
            return redirect(url_for('todo'))

    return render_template('todo.html', todos=todos)

if __name__ == '__main__':
    app.run(debug=True)
