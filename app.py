#Pelien toiminnallisuutta varten palvelin
#Tämän kautta pystyy nyt pelaamaan sitä alkukantasta kertotaulu peliä
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from database import get_random_question, register_user, get_game_instructions, check_user_credentials

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('frontPage.html')  # Tämä viittaa HTML-tiedostoon

@app.route('/firstscreen')
def firstscreen():
    return render_template('firstscreen.html')

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

#rekisteröitymisfunktio
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

#oppilaan kirjautumisfunktio
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
            return redirect(url_for('frontPage'))  # Ohjataan etusivulle
        else:
            return render_template('studentLogin.html', virhe="Virheellinen käyttäjätunnus tai salasana!")

    return render_template('studentLogin.html')

#opettajan kirjautumisfunktio
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
            return redirect(url_for('frontPage'))  # Ohjataan opettajan etusivulle
        else:
            return render_template('teacherLogin.html', virhe="Virheellinen käyttäjätunnus tai salasana!")

    return render_template('teacherLogin.html')


#kirjaudu ulos
@app.route('/logout')
def logout():
    rooli = session.get('rooli')  # Haetaan käyttäjän rooli
    session.clear()  # Tyhjennetään session-tiedot
    
    if rooli == "opettaja":
        return redirect(url_for('teacher_login_view'))
    else:
        return redirect(url_for('student_login_view'))

# Kuva reitti
@app.route('/Kuvat/<path:filename>')
def serve_images(filename):
    return send_from_directory('static/Kuvat', filename)

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

# ohjeiden hakufunktio peleille
@app.route('/get_instructions/<int:peli_id>')
def get_instructions(peli_id):
    instructions = get_game_instructions(peli_id)
    if instructions:
        return jsonify({"instructions": instructions})
    else:
        return jsonify({"instructions": "Ohjeita ei löytynyt"}), 404

@app.route('/gameScreen1/<int:game_id>')
def game_screen(game_id):
    return render_template("gameScreen1.html", game_id=game_id)

if __name__ == '__main__':
    app.run(debug=True)