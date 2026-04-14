from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            hiring_score REAL,
            raw_score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    answers = data['answers']
    company = data['company']

    raw_score = sum(answers)
    final_score = (raw_score / 40) * 100

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO responses (company, hiring_score, raw_score) VALUES (?, ?, ?)",
              (company, final_score, raw_score))
    conn.commit()
    conn.close()

    return jsonify({
        "score": final_score
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)