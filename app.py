#Pelien toiminnallisuutta varten palvelin
#Tämän kautta pystyy nyt pelaamaan sitä alkukantasta kertotaulu peliä
from flask import Flask, render_template, jsonify
from database import get_random_question

app = Flask(__name__)

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('mathMenu3rdGrade.html')  # Tämä viittaa HTML-tiedostoon

@app.route('/peli/<int:pelin_id>')  # Pelin ID voidaan välittää URL:ssä
def peli(pelin_id):
    # Tässä pelin_id voidaan käyttää hakemaan pelin tiedot tietokannasta
    return render_template('gameScreen1.html', pelin_id=pelin_id)

# Reitti tehtävien hakemiseen tietokannasta, pelin ID mukaan
@app.route('/new_question/<int:pelin_id>', methods=['GET'])
def new_question(pelin_id):
    question_data = get_random_question(pelin_id)  # Muokataan funktio hakemaan pelin mukaan
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