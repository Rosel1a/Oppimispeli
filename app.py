# Kuvaus: Tämä tiedosto sisältää pelisovelluksen pääsovelluslogiikan. 
# Sovellus on toteutettu Flask-kehyspohjaisena web-sovelluksena, joka käyttää tietokantaa kysymysten ja vastausten tallentamiseen. 

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import sys
import mysql.connector
from mysql.connector import connection
from database import get_random_question, register_user, get_game_instructions, check_user_credentials, save_player_answer, save_game_result, create_game_result
from database import get_all_students, get_all_classes, update_student_class, check_existing_group, create_new_group, get_teacher_class, get_class_id_by_name, get_opettaja_id_by_user_id
from database import get_student_by_id, get_student_by_class_id, get_class_name_by_id, get_results_by_oppilas_id, get_vastaukset_by_pelitulos_id, remove_student_from_class
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
sys.stderr = sys.stdout
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Pääsivun reitti
@app.route('/')
def index():
    return render_template('frontPage.html')  # Tämä viittaa HTML-tiedostoon

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

#reitti oppilaiden ryhmien hallintaan
@app.route('/group_management')
def group_management():
    return render_template('groupManagement.html')

#reitti ryhmienluontiin
@app.route('/group_selection')
def group_selection():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))

    user_id = session['userID']
    teacher_id = get_opettaja_id_by_user_id(user_id)

    oppilaat = get_all_students()
    #luokat = get_all_classes()
    teacher_groups = get_teacher_class(teacher_id)

     # Jos oppilaat ei ole tyhjä, jatka
    if not oppilaat:
        flash("Ei oppilaita löytynyt.", "danger")
    # Debug: Tulostetaan haetut luokat
    print(f"Opettajan {teacher_id} luokat: {teacher_groups}")

    return render_template('groupSelection.html', 
                           oppilaat=oppilaat, 
                           luokat=teacher_groups, 
                           teacher_groups=teacher_groups)

#reitti oppilasnäkymään
@app.route('/students_info')
def students_info():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))

    user_id = session['userID']
    teacher_id = get_opettaja_id_by_user_id(user_id)

    #oppilaat = get_student_by_class_id(2)
    oppilaat = []
    #luokat = get_all_classes()
    teacher_groups = get_teacher_class(teacher_id)

    return render_template('students.html', 
                           oppilaat=oppilaat, 
                           luokat=teacher_groups, 
                           teacher_groups=teacher_groups)

#reitti päivittyvälle oppilas listalle (oppilasnäkymässä)
@app.route('/students_list')
def students_list():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))

    user_id = session['userID']
    teacher_id = get_opettaja_id_by_user_id(user_id)

    # Haetaan valitun luokan oppilaat
    selected_class_id = request.args.get('luokkaID', default=None, type=int)
    print(f"Valittu luokkaID: {selected_class_id}")  # Debugi tuloste

    if selected_class_id:
        oppilaat = get_student_by_class_id(selected_class_id)
        print(f"Haetut oppilaat: {oppilaat}")  # Debugi tuloste
    else:
        oppilaat = []  # Jos luokkaa ei ole valittu, ei palauteta oppilaita

    # Palautetaan pelkästään oppilaslista HTML-muodossa
    return render_template('partials/student_list.html', oppilaat=oppilaat)
    

#reitti opettajiin
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
    rooli = request.form.get('rooli', 'oppilas')  # Tämä tulee piilotettuna inputina lomakkeessa

    #oppilaille myös:
    syntymapaiva = request.form.get('syntymapaiva')
    luokka = request.form.get('luokka')

    if register_user(etunimi, sukunimi, kirjautumistunnus, salasana, rooli, syntymapaiva, luokka):
        flash("Rekisteröinti onnistui!", "success")
        session['rooli'] = rooli
        if rooli == 'opettaja': 
            return redirect(url_for('teacher_menu'))
        else:
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
            return redirect(url_for('teacher_menu'))  # Ohjataan opettajan etusivulle
        else:
            return render_template('teacherLogin.html', virhe="Virheellinen käyttäjätunnus tai salasana!")

    return render_template('teacherLogin.html')

# Kirjaudu ulos
@app.route('/logout')
def logout():
    rooli = session.get('rooli')  # Haetaan käyttäjän rooli
    session.clear()  # Tyhjennetään session-tiedot
    
    if rooli == "opettaja":
        return redirect(url_for('firstscreen'))
    else:
        return redirect(url_for('firstscreen'))

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
    session['asked_questions'] = [] #tyhjä lista jo kysytyille tehtäville

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
    if 'asked_questions' not in session:
        session['asked_questions'] = []

    if session['question_count'] >= 10:
        return jsonify({'game_over': True, 'message': 'Peli on ohi!'}), 200

    question_data = get_random_question(pelin_id, session['asked_questions'])  # Muokataan funktio hakemaan pelin mukaan
    
    if question_data['tehtava_id']:
        session['asked_questions'].append(question_data['tehtava_id'])
        session['question_count'] += 1
        return jsonify(question_data)
    else:
        # Ei enää kysymyksiä jäljellä
        return jsonify({'game_over': True, 'message': 'Ei enää kysymyksiä!'}), 200

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
    correct_answers = session.get('correct_answers', 0)
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

#opettaja pystyy luomaan tällä luokan
@app.route('/create_group', methods=['POST'])
def create_group():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))
    
    user_id = session['userID']
    teacher_id = get_opettaja_id_by_user_id(user_id)  # Hae oikea opettajaID
    print("opettajan_id: ", teacher_id)

    data = request.get_json()  # Haetaan JSON-data pyynnöstä
    if not data or 'class_name' not in data:
        return jsonify({'success': False, 'message': 'Ryhmän nimi puuttuu.'}), 400

    class_name = data['class_name'].strip()
    if not class_name:
        return jsonify({'success': False, 'message': 'Ryhmän nimi ei voi olla tyhjä.'}), 400
    
    #class_name = data['class_name']
    # Tarkistetaan, onko opettajalla jo luokka
    existing_group = check_existing_group(teacher_id)

    if existing_group:
        # Jos opettajalla on jo luokka, ei voida luoda uutta
        flash('Sinulla on jo luokka luotuna. Et voi luoda uutta luokkaa.', 'error')
        return redirect(url_for('group_selection'))  # Uudelleenohjaa ryhmän hallintaan

    if not class_name:
        flash('Luokan nimi ei voi olla tyhjä.', 'error')
        return redirect(url_for('group_selection'))

    # Yritetään lisätä luokka ja hoitaa virheet oikein
    try:
        create_new_group(class_name, teacher_id)
        return jsonify({'success': True, 'message': 'Ryhmän luominen onnistui!'})
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Sinulla on jo luokka, et voi luoda toista.'}), 400
    except mysql.connector.Error as e:
        #connection.rollback()
        return jsonify({'success': False, 'message': f'Tietokantavirhe: {str(e)}'}), 500

#funktio jolla lisätään oppilas luokkaan
@app.route('/assign_class', methods=['POST'])
def assign_class():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))
    
    data = request.get_json()  # Haetaan JSON-data

    if not data:  # Tarkistetaan, että data on olemassa
        return jsonify({'success': False, 'message': 'Ei tietoja vastaanotettu.'}), 400

     # Debug: Tulostetaan vastaanotettu data
    print(f"Received data: {data}")

    oppilas_id = data.get('oppilas_id')  # Haetaan oppilas_id JSON-datasta
    uusi_luokka = data.get('luokka')

    # Debug tyypit ja sisältö
    print(f"oppilas_id: {oppilas_id} ({type(oppilas_id)}), uusi_luokka: {uusi_luokka} ({type(uusi_luokka)})")

    if not oppilas_id or not uusi_luokka:
        return jsonify({'success': False, 'message': 'Oppilas ID tai luokan nimi puuttuu.'}), 400

    try:
        #luokka_id = get_class_id_by_name(uusi_luokka)
        
        #if not luokka_id:
            #return jsonify({'success': False, 'message': 'Luokkaa ei löytynyt.'}), 400

        # Päivitetään oppilaan luokka
        update_student_class(oppilas_id, uusi_luokka)

        return jsonify({'success': True, 'message': 'Oppilas lisätty luokkaan onnistuneesti!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Virhe: {str(e)}'}), 500

#oppilaan poistamiseksi ryhmästä  
@app.route('/remove_from_class', methods=['POST'])
def remove_from_class():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': 'Ei tietoja vastaanotettu.'}), 400

    oppilas_id = data.get('oppilas_id')
    luokka_id = data.get('luokka')

    print(f"Poistetaan oppilas {oppilas_id} luokasta {luokka_id}")

    if not oppilas_id or not luokka_id:
        return jsonify({'success': False, 'message': 'Oppilas ID tai luokan ID puuttuu.'}), 400

    try:
        # Funktio, joka poistaa oppilaan luokasta tietokannasta
        remove_student_from_class(oppilas_id, luokka_id)
        return jsonify({'success': True, 'message': 'Oppilas poistettu luokasta onnistuneesti!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Virhe: {str(e)}'}), 500
    

# Flask reitti oppilaan tietojen hakemiseksi
@app.route('/get_student_info/<int:oppilas_id>', methods=['GET'])
def get_student_info(oppilas_id):
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        flash("Kirjaudu sisään opettajana!", "danger")
        return redirect(url_for('teacher_login'))

    # Hae oppilaan tiedot tietokannasta
    oppilas = get_student_by_id(oppilas_id)  # Tämä on esimerkki, sinulla voi olla oma funktio

    if not oppilas:
        return jsonify({'success': False, 'message': 'Oppilasta ei löytynyt.'}), 404

    luokka_nimi = get_class_name_by_id(oppilas['luokkaID'])

    # Palautetaan oppilaan tiedot JSON-muodossa
    return jsonify({
        'etunimi': oppilas['etunimi'],
        'sukunimi': oppilas['sukunimi'],
        'syntymapaiva': oppilas['syntymapaiva'],
        'luokka': luokka_nimi
    })

#hakee valitun oppilaan pelitulokset 
@app.route('/get_student_results')
def get_student_results():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        return jsonify({'error': 'Unauthorized access'}), 403

    oppilas_id = request.args.get('oppilasID', default=None, type=int)
    if oppilas_id is None:
        return jsonify({'error': 'No student ID provided'}), 400

    # Haetaan pelitulokset
    results = get_results_by_oppilas_id(oppilas_id)
    return jsonify(results)

#hakee pelin yksittäiset vastaukset pelitulos_idn mukaan
@app.route('/get_pelaajan_vastaukset')
def get_pelaajan_vastaukset():
    if 'userID' not in session or session.get('rooli') != 'opettaja':
        return jsonify({'error': 'Unauthorized access'}), 403

    pelitulos_id = request.args.get('pelitulosID', default=None, type=int)
    if pelitulos_id is None:
        return jsonify({'error': 'No pelitulos ID provided'}), 400

    # Haetaan vastaukset
    results = get_vastaukset_by_pelitulos_id(pelitulos_id)
    return jsonify(results)

#  Virheiden käsittely
if __name__ == '__main__':
    app.run(debug=True)