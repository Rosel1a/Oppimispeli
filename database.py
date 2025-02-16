#SQL-tietokantayhteys
# 

import mysql.connector

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
#1-kertotaulu peli kysymykset arpoo tietokannasta
def get_random_question():
    connection = get_db_connection(host, user, password, database)
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

get_db_connection(host, user, password, database)