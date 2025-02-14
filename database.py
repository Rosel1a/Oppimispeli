#SQL-tietokantayhteys
#

import mysql.connector

# Yhdistä MySQL-tietokantaan
def get_db_connection():
    db_connection = mysql.connector.connect(
        host="localhost",  # MySQL-palvelimen isäntä (usein 'localhost')
        user="root",       # Käyttäjänimi (muuta tarpeen mukaan)
        password="Salasana1",  # MySQL:n salasana
        database="oppimispeli"   # Tietokannan nimi
    )
    return db_connection

# Luo kursori, jolla voidaan suorittaa SQL-kyselyt
#cursor = db_connection.cursor()

# Esimerkki: Suoritetaan SQL-kysely ja haetaan tietoa
#cursor.execute("SHOW TABLES")

# Tulostetaan taulujen nimet
##for table in cursor.fetchall():
    #print(table[0])  # Tulostetaan taulun nimi

# Tarkistetaan, että tehtävät on lisätty
#cursor.execute("SELECT * FROM tehtava")
#print("Lisätty testi tehtävät:")
#for row in cursor.fetchall():
    #print(row)

# Funktio, joka palauttaa satunnaisen kysymyksen tietokannasta
#1-kertotaulu peli kysymykset arpoo tietokannasta
def get_random_question():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT * FROM tehtava ORDER BY RAND() LIMIT 1"  # Hakee satunnaisen kysymyksen
    cursor.execute(query)
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


# Sulje yhteys ja kursori
#cursor.close()
#db_connection.close()