#SQL-tietokantayhteys
# Tämä tiedosto sisältää funktiot, jotka liittyvät tietokantaan ja sen käsittelyyn.
import mysql.connector
import sys
from flask import session

# Tämä on vain esimerkki, joka ei ole turvallinen tuotantokäytössä!
# Käytä salasanojen turvalliseen käsittelyyn esim. Flask-Bcrypt -kirjastoa
# https://flask-bcrypt.readthedocs.io/en/latest/
#
# Esimerkki:       
# from flask import Flask
#
# app = Flask(__name__)
# bcrypt = Bcrypt(app)
#
# # Salasanan hashaus
# hashed_password = bcrypt.generate_password_hash('salasana').decode('utf-8')
#
# # Salasanan tarkistus
# is_valid = bcrypt.check_password_hash(hashed_password, 'salasana')
###from flask_bcrypt import Bcrypt

host = "85.23.94.251"      # Esim. "123.45.67.89" 
user = "saaga"    # MySQL-käyttäjänimi
password = "salasana2"    # MySQL-salasana
database = "oppimispeli"  # Tietokannan nimi

# Yhdistä MySQL-tietokantaan
def get_db_connection(host, user, password, database):
    try:
        db_connection = mysql.connector.connect(
            host=host,         # MySQL-palvelimen isäntä
            user=user,         # Käyttäjänimi
            password=password, # MySdQL:n salasana
            database=database  # Tietokannan nimi
        )
        if db_connection.is_connected():
            print("✅ Yhteys onnistui!")
            
            cursor = db_connection.cursor()
            cursor.execute("SHOW TABLES;")

            for table in cursor.fetchall():
                print(table)
            
        return db_connection
    
    except mysql.connector.Error as err:
        # Virheiden käsittely
        print(f"Yhteys epäonnistui: {err}")
        return None

# Funktio, joka palauttaa satunnaisen kysymyksen tietokannasta
def get_random_question(pelin_id):
    connection = get_db_connection(host, user, password, database)
    cursor = connection.cursor(dictionary=True)

    # Käytetään pelin ID:tä kyselyssä
    query = "SELECT * FROM tehtava WHERE Pelit_peliID = %s ORDER BY RAND() LIMIT 1"
    cursor.execute(query, (pelin_id,))  # pelin_id lisätään parametrina kyselyyn
    question = cursor.fetchone()
    
    cursor.close()
    connection.close()

    if question:
        return {
            'question': question['kysymys'],
            'answer': question['oikea_vastaus'],
            'answer_type': 'number' if question['oikea_vastaus'].isdigit() else 'text',
            'tehtava_id': question['tehtavaID']  # Lisää tehtava_id tähän
        }
    else:
        return {'question': 'No questions found', 'answer': '', 'answer_type': 'text', 'tehtava_id': None}
    
# Funktio pelin ohjeiden hakemiseen
def get_game_instructions(peli_id):
    conn = get_db_connection(host, user, password, database)
    if conn is None:
        return None  # Jos yhteys epäonnistui, palauta None

    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT ohje FROM pelit WHERE peliID = %s"
        cursor.execute(sql, (peli_id,))
        result = cursor.fetchone()
        return result["ohje"] if result else None
    except Error as e:
        print(f"Virhe ohjeiden hakemisessa: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
    
# Funktio käyttäjän rekisteröitymiselle
def register_user(etunimi, sukunimi, kirjautumistunnus, salasana, rooli, syntymapaiva=None, luokka=None):
    conn = get_db_connection(host, user, password, database)
    cursor = conn.cursor()

    try:
        # 🔹 1. Lisää käyttäjä user-tauluun
        sql = "INSERT INTO user (etunimi, sukunimi, kirjautumistunnus, salasana, rooli, created_at) VALUES (%s, %s, %s, %s, %s, NOW())"
        values = (etunimi, sukunimi, kirjautumistunnus, salasana, rooli)
        cursor.execute(sql, values)
        conn.commit()

        # 🔹 2. Hae userID
        user_id = cursor.lastrowid

        # 🔹 3. Lisää käyttäjä opettaja- tai oppilastauluun
        if rooli == "opettaja":
            sql_opettaja = "INSERT INTO opettaja (User_userID) VALUES (%s)"
            cursor.execute(sql_opettaja, (user_id,))
        elif rooli == "oppilas":
            if syntymapaiva is None or luokka is None:
                raise ValueError("Syntymäpäivä ja luokka ovat pakollisia oppilaille!")

            sql_oppilas = "INSERT INTO oppilas (User_userID, syntymapaiva, luokka) VALUES (%s, %s, %s)"
            cursor.execute(sql_oppilas, (user_id, syntymapaiva, luokka))

        conn.commit()
        return True  # Onnistui
    except mysql.connector.Error as err:
        print(f"Virhe: {err}")
        return False  # Epäonnistui
    finally:
        cursor.close()
        conn.close()

# Kirjautumista varten
def check_user_credentials(kirjautumistunnus, salasana, rooli):
    """ Tarkistaa käyttäjän tunnukset ja palauttaa käyttäjätiedot roolin perusteella """
    conn = get_db_connection(host, user, password, database)
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    login_user = None  # Alustetaan muuttuja ennen try-lohkoa

    try:
        sql = "SELECT userID, salasana, rooli FROM user WHERE kirjautumistunnus = %s AND rooli = %s"
        cursor.execute(sql, (kirjautumistunnus, rooli))
        login_user = cursor.fetchone()

        #if user and check_password_hash(user["salasana"], salasana):
        if login_user and login_user["salasana"] == salasana:
            # Jos käyttäjä on oppilas, haetaan myös oppilasID
            if rooli == "oppilas":
                cursor.execute("SELECT oppilasID FROM oppilas WHERE User_userID = %s", (login_user["userID"],))
                oppilas_data = cursor.fetchone()
                
                if oppilas_data:
                    login_user["oppilasID"] = oppilas_data["oppilasID"]
                else:
                    login_user["oppilasID"] = None  # Jos oppilasta ei löydy, asetetaan None
            else:
                login_user["oppilasID"] = None  # Opettajilla ei ole oppilasID:tä

            return login_user  # Palautetaan käyttäjän tiedot
        else:
            return None  # Väärä käyttäjätunnus, salasana tai rooli
    except Error as e:
        print(f"Virhe kirjautumisessa: {e}")
        return None
    finally:
        cursor.close()
        conn.close()   
        
# Tallennetaan pelaajan vastaus tietokantaan
def save_player_answer(pelitulos_id, tehtava_id, pelaajan_vastaus, oikein):
    """ Tallentaa pelaajan vastauksen tietokantaan. """
    connection = get_db_connection(host, user, password, database)
    if not connection:
        return False
    
    cursor = connection.cursor()
    query = """
        INSERT INTO pelaajan_vastaus (Pelitulos_pelitulosID, Tehtava_tehtavaID, pelaajan_vastaus, onko_oikein, aikaleima)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(query, (pelitulos_id, tehtava_id, pelaajan_vastaus, oikein))
    connection.commit()
    
    cursor.close()
    connection.close()
    return True

def create_game_result(oppilas_id, peli_id):
    """ Luo uuden pelituloksen tietokantaan ja palauttaa sen ID:n. """
    connection = get_db_connection(host, user, password, database)
    if not connection:
        return None
    
    cursor = connection.cursor()
    query = """
        INSERT INTO pelitulos (Oppilas_oppilasID, Pelit_peliID, pisteet, kysymys_maara, oikeat_vastaukset, peliaika, pvm)
        VALUES (%s, %s, 0, 0, 0, 0, NOW())
    """
    cursor.execute(query, (oppilas_id, peli_id))
    connection.commit()
    
    pelitulos_id = cursor.lastrowid  # Haetaan juuri lisätyn pelituloksen ID
    cursor.close()
    connection.close()
    
    session['correct_answers'] = 0  

    return pelitulos_id

# Tallennetaan pelin lopputulos
def save_game_result(pelitulos_id, pisteet, kysymys_maara, oikeat_vastaukset):
    """ Tallentaa pelituloksen tietokantaan. """
    connection = get_db_connection(host, user, password, database)
    if not connection:
        sys.stderr.write("Virhe: ei tietokantayhteyttä\n")  # 🔍 Debug
        return False
    
    cursor = connection.cursor()
    sys.stderr.write(f"UPDATE pelitulos SET pisteet={pisteet}, kysymys_maara={kysymys_maara}, oikeat_vastaukset={oikeat_vastaukset} WHERE pelitulosID={pelitulos_id}")
    
    query = """
        UPDATE pelitulos
        SET pisteet = %s, kysymys_maara = %s, oikeat_vastaukset = %s, peliaika = 0, pvm = NOW()
        WHERE pelitulosID = %s
    """
    cursor.execute(query, (pisteet, kysymys_maara, oikeat_vastaukset, pelitulos_id))
    connection.commit()
    
    cursor.close()
    connection.close()
    return True

get_db_connection(host, user, password, database)