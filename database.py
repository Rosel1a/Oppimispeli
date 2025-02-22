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

# LUE!! tästä jokainen muokkaa ainoastaan user ja password kohtaa !
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
# Arpoo kysymykset tietokannasta
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

get_db_connection(host, user, password, database)