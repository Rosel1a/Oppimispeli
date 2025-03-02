#SQL-tietokantayhteys
# Tämä tiedosto sisältää funktiot, jotka liittyvät tietokantaan ja sen käsittelyyn.
import mysql.connector

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
            'answer_type': 'number' if question['oikea_vastaus'].isdigit() else 'text'
        }
    else:
        return {'question': 'No questions found', 'answer': '', 'answer_type': 'text'}
    
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
    
#funktio käyttäjän rekisteröitymiselle
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

#kirjautumista varten
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
            return login_user  # Palautetaan käyttäjän tiedot (ID ja rooli)
        else:
            return None  # Väärä käyttäjätunnus, salasana tai rooli
    except Error as e:
        print(f"Virhe kirjautumisessa: {e}")
        return None
    finally:
        cursor.close()
        conn.close()   

get_db_connection(host, user, password, database)