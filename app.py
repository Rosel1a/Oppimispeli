# Kuvaus: Tämä tiedosto sisältää pelisovelluksen pääsovelluslogiikan. 
# Sovellus on toteutettu Flask-kehyspohjaisena web-sovelluksena, joka käyttää tietokantaa kysymysten ja vastausten tallentamiseen. 

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import sys
from database import get_random_question, register_user, get_game_instructions, check_user_credentials, save_player_answer, save_game_result, create_game_result
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
sys.stderr = sys.stdout
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('teacherMenu.html')  # Tämä viittaa HTML-tiedostoon

# Reitti kirjautumissivulle
@app.route('/firstscreen')
def firstscreen():
    return render_template('firstscreen.html')

# Reitti etusivulle
@app.route('/frontPage')
def frontPage():
    return render_template('frontPage.html')

# Opettajan kirjautuminen
@app.route('/teacher_login')
def teacher_login():
    return render_template('teacherLogIn.html')

# Opiskelijan kirjautuminen
@app.route('/student_login')
def student_login():
    return render_template('studentLogIn.html')

#reitti oppilaiden hallintaan
@app.route('/group_management')
def group_management():
    return render_template('groupManagement.html')

#reitti oppilaisiin
@app.route('/students_info')
def students_info():
    return render_template('students.html')

#reitti oppilaisiin
@app.route('/teacher_menu')
def teacher_menu():
    return render_template('teacherMenu.html')

# Rekisteröitymisfunktio
@app.route('/register', methods=['POST'])
def register():
    etunimi = request.form['etunimi']
    sukunimi = request.form['sukunimi']
    kirjautumistunnus = request.form['kirjautumistunnus']
    salasana = request.form['salasana']
    rooli = request.form['rooli']  # Tämä tulee piilotettuna inputina lomakkeessa

    #oppilaille myös:
    syntymapaiva = request.form.get('syntymapaiva')
    luokka = request.form.get('luokka')

    if register_user(etunimi, sukunimi, kirjautumistunnus, salasana, rooli, syntymapaiva, luokka):
        flash("Rekisteröinti onnistui!", "success")
        return redirect(url_for('frontPage'))
    else:
        flash("Rekisteröinti epäonnistui!", "danger")
        return redirect(url_for('firstscreen'))

# Oppilaan kirjautumisfunktio
@app.route('/student_login', methods=['GET', 'POST'])
def student_login_view():
    logged_in_user = None

    if request.method == 'POST':
        kirjautumistunnus = request.form.get('kirjautumistunnus')
        salasana = request.form.get('salasana')

        # Tarkistetaan käyttäjätiedot tietokannasta
        logged_in_user = check_user_credentials(kirjautumistunnus, salasana, "oppilas")

        if logged_in_user:
            session['userID'] = logged_in_user['userID']  # Tallennetaan käyttäjä sessioniin
            session['rooli'] = 'oppilas'  

            if logged_in_user['oppilasID']:
                session['oppilasID'] = logged_in_user['oppilasID']  # Tallennetaan oppilaan ID
                print("Session userID:", session.get('userID'))
                print("Session oppilasID:", session.get('oppilasID'))

                if 'userID' in session:
                    print("Käyttäjä on kirjautunut sisään:", session['userID'])
                else:
                    print("Ei aktiivista sessionia")
            return redirect(url_for('frontPage'))  # Ohjataan etusivulle
        else:
            return render_template('studentLogin.html', virhe="Virheellinen käyttäjätunnus tai salasana!")

    return render_template('studentLogin.html')

# Opettajan kirjautumisfunktio
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login_view():
    logged_in_user = None

    if request.method == 'POST':
        kirjautumistunnus = request.form.get('kirjautumistunnus')
        salasana = request.form.get('salasana')

        # Tarkistetaan käyttäjätiedot tietokannasta, roolina "opettaja"
        logged_in_user = check_user_credentials(kirjautumistunnus, salasana, "opettaja")

        if logged_in_user:
            session['userID'] = logged_in_user['userID']  # Tallennetaan käyttäjä sessioniin
            session['rooli'] = 'opettaja'  
            print("Session userID:", session.get('userID'))
            return redirect(url_for('frontPage'))  # Ohjataan opettajan etusivulle
        else:
            return render_template('teacherLogin.html', virhe="Virheellinen käyttäjätunnus tai salasana!")

    return render_template('teacherLogin.html')

# Kirjaudu ulos
@app.route('/logout')
def logout():
    rooli = session.get('rooli')  # Haetaan käyttäjän rooli
    session.clear()  # Tyhjennetään session-tiedot
    
    if rooli == "opettaja":
        return redirect(url_for('teacher_login_view'))
    else:
        return redirect(url_for('student_login_view'))

# Kuva reitti
@app.route('/kuvat/<path:filename>')
def serve_images(filename):
    return send_from_directory('static/kuvat', filename)

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
        return redirect(url_for('index'))  # Ohjataan pääsivulle

# Pelinäkymän reitti
@app.route('/gameScreen1/<int:game_id>')
def game_screen(game_id):
    return render_template("gameScreen1.html", game_id=game_id)

# Pelin aloitusreitti
@app.route('/peli/<int:pelin_id>')  # Pelin ID voidaan välittää URL:ssä
def peli(pelin_id):
    # Tässä pelin_id voidaan käyttää hakemaan pelin tiedot tietokannasta
    session['question_count'] = 0  # Alustetaan kysymysten laskuri
    session['score'] = 0

    # Luodaan pelitulos ID peliä varten
    pelitulos_id = create_game_result(session.get('oppilasID'), pelin_id)
    session['pelitulos_id'] = pelitulos_id

    return render_template('gameScreen1.html', pelin_id=pelin_id)

# Ohjeiden hakufunktio peleille
@app.route('/get_instructions/<int:peli_id>')
def get_instructions(peli_id):
    instructions = get_game_instructions(peli_id)
    if instructions:
        return jsonify({"instructions": instructions})
    else:
        return jsonify({"instructions": "Ohjeita ei löytynyt"}), 404

# Reitti tehtävien hakemiseen tietokannasta, pelin ID mukaan
@app.route('/new_question/<int:pelin_id>', methods=['GET'])
def new_question(pelin_id):
    if 'question_count' not in session:
        session['question_count'] = 0

    if session['question_count'] >= 10:
        return jsonify({'game_over': True, 'message': 'Peli on ohi!'}), 200

    question_data = get_random_question(pelin_id)  # Muokataan funktio hakemaan pelin mukaan
    session['question_count'] += 1
    return jsonify(question_data)

# Vastauksen tarkistusreitti
@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')
    peli_id = data.get('peli_id')
    tehtava_id = data.get('tehtava_id')  # Lisätään tehtava_id

    if 'score' not in session:
        session['score'] = 0  # Alustetaan pisteet

    if 'correct_answers' not in session:
        session['correct_answers'] = 0  # Alustetaan oikeat vastaukset

    is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()

    if is_correct:
        session['score'] += 1
        session['correct_answers'] += 1  # Lisätään oikea vastaus

    # Tallennetaan vastaus tietokantaan
    pelitulos_id = session.get('pelitulos_id')  # Pitää olla luotu ennen kuin vastauksia tallennetaan
    save_player_answer(pelitulos_id, tehtava_id, user_answer, is_correct)

    return jsonify({"correct": is_correct, "score": session['score'], "correct_answers": session['correct_answers']})

# Pelin lopetusreitti
@app.route('/end_game', methods=['POST'])
def end_game():
    print("Session sisältö ennen tarkistusta:", session)  # Tulostetaan session sisältö
    if 'userID' not in session:
        print("⚠️ Virhe: Käyttäjä ei ole kirjautunut!")
        return jsonify({'error': 'Ei käyttäjää kirjautuneena'}), 403

    pelitulos_id = session.get('pelitulos_id')  # Oikea pelitulos_id, joka on luotu aiemmin
    if not pelitulos_id:
        sys.stderr.write("Virhe: pelitulos_id ei löydy sessionista!\n")  # Näkyy virhelokissa
        return jsonify({'error': 'Pelitulos ID puuttuu!'}), 400  # Varmistetaan, että pelitulos_id on olemassa

    data = request.get_json()
    final_score = data.get('final_score', 0)
    correct_answers = data.get('correct_answers', 0)
    question_count = session.get('question_count', 0)

    sys.stderr.write(f"Tallennetaan tulos: pelitulos_id={pelitulos_id}, pisteet={final_score}, kysymykset={question_count}, oikein={correct_answers}")

    success = save_game_result(pelitulos_id, final_score, question_count, correct_answers)  # Käytä oikeaa pelitulos_id:tä

    if not success:
        return jsonify({'error': 'Tietokantavirhe tallennettaessa pelitulosta'}), 500

    # Tyhjennetään sessionin pisteet ja kysymysten määrä
    session.pop('score', None)
    session.pop('question_count', None)
    session.pop('correct_answers', None)

    return jsonify({'message': f'Peli päättyi, pisteet tallennettu! Oikein meni {correct_answers}/10', 'final_score': final_score})

#  Virheiden käsittely
if __name__ == '__main__':
    app.run(debug=True)