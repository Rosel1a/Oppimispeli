#Pelien toiminnallisuutta varten palvelin
#Tämän kautta pystyy nyt pelaamaan sitä alkukantasta kertotaulu peliä
from flask import Flask, render_template, jsonify
from database import get_random_question

app = Flask(__name__)

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('frontPage.html')  # Tämä viittaa HTML-tiedostoon

@app.route('/teacher_login')
def teacher_login():
    return render_template('teacherLogIn.html')

@app.route('/student_login')
def student_login():
    return render_template('studentLogIn.html')

# Matematiikan valikko
@app.route('/math_menu/<int:grade>')
def math_menu(grade):
    if grade == 3:
        return render_template('mathMenu3rdGrade.html')
    elif grade == 4:
        return render_template('mathMenu4rdGrade.html')
    elif grade == 5:
        return render_template('mathMenu5rdGrade.html')
    elif grade == 6:
        return render_template('mathMenu6rdGrade.html')
    else:
        return redirect(url_for('index'))  # Redirects to a default page or 404 if grade is invalid

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