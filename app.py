#pelien toiminnallisuutta varten palvelin
#tän kautta pystyy nyt pelaamaan sitä alkukantasta kertotaulu peliä
from flask import Flask, render_template, jsonify
from database import get_random_question

app = Flask(__name__)

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('index.html')  # Tämä viittaa HTML-tiedostoon

@app.route('/peli1')
def peli1():
    # Tämä reitti palvelee peli1.html-sivua
    return render_template('peli1.html')

# Reitti tehtävien hakemiseen tietokannasta
@app.route('/new_question', methods=['GET'])
def new_question():
    question_data = get_random_question()
    return jsonify(question_data)

# Vastauksen tarkistus
@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user_answer = data['user_answer']
    correct_answer = data['correct_answer']
    
    # Tarkistetaan vastaus (olettaen että vastaus on oikein jos se täsmää)
    is_correct = str(user_answer) == str(correct_answer)
    
    return jsonify({"correct": is_correct})

if __name__ == '__main__':
    app.run(debug=True)