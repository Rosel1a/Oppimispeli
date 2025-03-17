#SQL-tietokantayhteys
# Tämä tiedosto sisältää funktiot, jotka liittyvät tietokantaan ja sen käsittelyyn.
import mysql.connector
from mysql.connector import pooling
import sys
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

# Määritellään yhteyspooli 
#"host": "localhost",
#    "user": "root",
#    "password": "kissa",
#   "database": "oppimispeli2"
dbconfig = {    
    "host": "123.45.67.89",      # Esim. "123.45.67.89" 
    "user" : "saaga",    # MySQL-käyttäjänimi
    "password": "Salasana2" ,   # MySQL-salasana
    "database" : "oppimispeli"  # Tietokannan nimi
}

connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **dbconfig
)

def get_db_connection():
    try:
        connection = connection_pool.get_connection()
        if connection.is_connected():
            print("✅ Yhteys onnistui!")
        return connection
    except mysql.connector.Error as err:
        print(f"Yhteys epäonnistui: {err}")
        return None

# Funktio, joka palauttaa satunnaisen kysymyksen tietokannasta
def get_random_question(pelin_id, asked_question_ids):
    connection = get_db_connection()
    if not connection:
        print("Tietokantayhteys epäonnistui!")
        return {'question': 'No questions found', 'answer': '', 'answer_type': 'text', 'tehtava_id': None}
    
    try:
        cursor = connection.cursor(dictionary=True)

        # Suodatetaan jo kysytyt kysymykset
        if asked_question_ids:
            placeholders = ','.join(['%s'] * len(asked_question_ids))
            query = f"""
                SELECT * FROM tehtava
                WHERE Pelit_peliID = %s AND tehtavaID NOT IN ({placeholders})
                ORDER BY RAND() LIMIT 1
            """
            params = [pelin_id] + asked_question_ids
        else:
            query = "SELECT * FROM tehtava WHERE Pelit_peliID = %s ORDER BY RAND() LIMIT 1"
            params = [pelin_id]

        cursor.execute(query, params)
        question = cursor.fetchone()

        if question:
            return {
                'question': question['kysymys'],
                'answer': question['oikea_vastaus'],
                'answer_type': 'number' if question['oikea_vastaus'].isdigit() else 'text',
                'tehtava_id': question['tehtavaID']
            }
        else:
            return {'question': 'No questions found', 'answer': '', 'answer_type': 'text', 'tehtava_id': None}

    finally:
        cursor.close()
        connection.close()
    
# Funktio pelin ohjeiden hakemiseen
def get_game_instructions(peli_id):
    connection = get_db_connection()
    if connection is None:
        return None  # Jos yhteys epäonnistui, palauta None

    cursor = connection.cursor(dictionary=True)
    try:
        sql = "SELECT ohje FROM pelit WHERE peliID = %s"
        cursor.execute(sql, (peli_id,))
        result = cursor.fetchone()
        return result["ohje"] if result else None
    except mysql.connector.Error as e:
        print(f"Virhe ohjeiden hakemisessa: {e}")
        return None
    finally:
        cursor.close()
        connection.close()
    
# Funktio käyttäjän rekisteröitymiselle
def register_user(etunimi, sukunimi, kirjautumistunnus, salasana, rooli, syntymapaiva=None, luokka=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        #luodaan salattu salasana
        hashed_salasana = generate_password_hash(salasana)
        # 🔹 1. Lisää käyttäjä user-tauluun
        sql = "INSERT INTO user (etunimi, sukunimi, kirjautumistunnus, salasana, rooli, created_at) VALUES (%s, %s, %s, %s, %s, NOW())"
        values = (etunimi, sukunimi, kirjautumistunnus, hashed_salasana, rooli)
        cursor.execute(sql, values)
        connection.commit()

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

        connection.commit()
        return True  # Onnistui
    except mysql.connector.Error as err:
        print(f"Virhe: {err}")
        return False  # Epäonnistui
    finally:
        cursor.close()
        connection.close()

# Kirjautumista varten
def check_user_credentials(kirjautumistunnus, salasana, rooli):
    """ Tarkistaa käyttäjän tunnukset ja palauttaa käyttäjätiedot roolin perusteella """
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    login_user = None  # Alustetaan muuttuja ennen try-lohkoa

    try:
        sql = "SELECT userID, salasana, rooli FROM user WHERE kirjautumistunnus = %s AND rooli = %s"
        cursor.execute(sql, (kirjautumistunnus, rooli))
        login_user = cursor.fetchone()

        
        #if login_user and login_user["salasana"] == salasana:
        if login_user and check_password_hash(login_user["salasana"], salasana):
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
    except mysql.connector.Error as e:
        print(f"Virhe kirjautumisessa: {e}")
        return None
    finally:
        cursor.close()
        connection.close()   
        
# Tallennetaan pelaajan vastaus tietokantaan
def save_player_answer(pelitulos_id, tehtava_id, pelaajan_vastaus, oikein):
    """ Tallentaa pelaajan vastauksen tietokantaan. """
    connection = get_db_connection()
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
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor()
    query = """
        INSERT INTO pelitulos (Oppilas_oppilasID, Pelit_peliID, pisteet, kysymys_maara, oikeat_vastaukset, pvm)
        VALUES (%s, %s, 0, 0, 0, NOW())
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
    connection = get_db_connection()
    if not connection:
        sys.stderr.write("Virhe: ei tietokantayhteyttä\n")  # 🔍 Debug
        return False
    
    cursor = connection.cursor()
    sys.stderr.write(f"UPDATE pelitulos SET pisteet={pisteet}, kysymys_maara={kysymys_maara}, oikeat_vastaukset={oikeat_vastaukset} WHERE pelitulosID={pelitulos_id}")
    
    query = """
        UPDATE pelitulos
        SET pisteet = %s, kysymys_maara = %s, oikeat_vastaukset = %s, pvm = NOW()
        WHERE pelitulosID = %s
    """
    cursor.execute(query, (pisteet, kysymys_maara, oikeat_vastaukset, pelitulos_id))
    connection.commit()
    
    cursor.close()
    connection.close()
    return True

# Tarkistaa, onko opettajalla jo luokka
def check_existing_group(teacher_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM luokka WHERE Opettaja_opettajaID = %s", (teacher_id,))
    existing_group = cursor.fetchone()

    cursor.close()
    connection.close()
    
    return existing_group

def get_opettaja_id_by_user_id(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    print(f"Hakee opettajaID käyttäjäID:llä {user_id}")
    
    cursor.execute("SELECT opettajaID FROM opettaja WHERE User_userID = %s", (user_id,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    return result['opettajaID'] if result else None

# Hakee opettajan luomat ryhmät
def get_teacher_class(teacher_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT luokkaID, luokka_nimi FROM luokka WHERE Opettaja_opettajaID = %s
    """
    cursor.execute(query, (teacher_id,))
    luokat = cursor.fetchall()

    # Debug: Tulostetaan haetut luokat
    print(f"Haetut luokat: {luokat}")

    cursor.close()
    connection.close()
    return luokat

# Luo uusi luokka tietokantaan
def create_new_group(class_name, teacher_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    print("opettajan ID on vieläkin: ", teacher_id)

    try:
        cursor.execute(
            "INSERT INTO luokka (luokka_nimi, Opettaja_opettajaID) VALUES (%s, %s)", 
            (class_name, teacher_id)
        )
        connection.commit()  # Varmistetaan, että muutos tallentuu
    except mysql.connector.IntegrityError as e:
        print(f"IntegrityError: {e}")  # Esim. UNIQUE rajoite
        connection.rollback()  # Perutaan transaktio
        raise e  # Lähetetään virhe takaisin Flask-reitille
    except mysql.connector.Error as e:
        print(f"DatabaseError: {e}")  # Muut tietokantavirheet, esim. lukitus
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

#opiskelijan poistamiseksi ryhmästä
def remove_student_from_class(oppilas_id, luokka_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Esimerkki SQL:stä — muokkaa taulujen ja sarakkeiden nimet sopiviksi
    sql = """
        UPDATE oppilas
        SET luokkaID = NULL
        WHERE oppilasID = %s AND luokkaID = %s
    """
    cursor.execute(sql, (oppilas_id, luokka_id))
    connection.commit()
    cursor.close()
    connection.close()


#hakee kaikki oppilaat ja heidän luokat
def get_all_students():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT o.oppilasID, u.etunimi, u.sukunimi, o.luokka
        FROM oppilas o
        JOIN user u ON o.User_userID = u.userID
    """
    cursor.execute(query)
    students = cursor.fetchall()

    cursor.close()
    connection.close()
    return students

def get_student_by_id(oppilas_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # SQL-kysely oppilaan tietojen hakemiseksi
        #query = "SELECT etunimi, sukunimi, syntymapaiva, luokkaID FROM oppilas WHERE oppilasID = %s"
        query = """
            SELECT
                u.etunimi,
                u.sukunimi,
                o.syntymapaiva,
                o.luokkaID
            FROM oppilas o
            JOIN user u ON o.User_userID = u.userID
            WHERE o.oppilasID = %s
        """
        cursor.execute(query, (oppilas_id,))
        
        # Haetaan tulokset
        oppilas = cursor.fetchone()

        if not oppilas:
            # Jos oppilasta ei löydy
            return None

        return oppilas  # Palautetaan oppilaan tiedot sanakirjana

    except mysql.connector.Error as err:
        print(f"Virhe tietokannan kyselyssä: {err}")
        return None

    finally:
        cursor.close()
        connection.close()

def get_student_by_class_id(luokkaID):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # SQL-kysely oppilaiden hakemiseksi luokkaID:n perusteella
        query = """
            SELECT
                o.oppilasID,
                u.etunimi,
                u.sukunimi,
                o.syntymapaiva,
                o.luokkaID
            FROM oppilas o
            JOIN user u ON o.User_userID = u.userID
            WHERE o.luokkaID = %s
        """
        cursor.execute(query, (luokkaID,))  # Käytetään parametrisoitua kyselyä SQL-injektion estämiseksi
    
        students = cursor.fetchall()  # Haetaan kaikki tulokset
        
        # Debug: Tarkistetaan, että oppilaat saadaan oikein
        print(f"Haetut oppilaat: {students}")

        return students  # Palautetaan oppilaat listana

    except mysql.connector.Error as err:
        print(f"Virhe tietokannan kyselyssä: {err}")
        return []  # Palautetaan tyhjä lista virheen sattuessa

    finally:
        cursor.close()
        connection.close()
        
#hakee kaikki käytössä olevat luokat
def get_all_classes():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT luokkaID, luokka_nimi FROM luokka"
    cursor.execute(query)
    classes = cursor.fetchall()

    cursor.close()
    connection.close()
    return classes

# Funktio, joka hakee luokan ID:n luokan nimen perusteella
def get_class_id_by_name(class_name):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = "SELECT luokkaID FROM luokka WHERE luokka_nimi = %s"
    cursor.execute(query, (class_name,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result['luokkaID'] if result else None

def get_class_name_by_id(luokkaID):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # SQL-kysely luokan nimen hakemiseksi luokkaID:n perusteella
        query = "SELECT luokka_nimi FROM luokka WHERE luokkaID = %s"
        cursor.execute(query, (luokkaID,))
        
        # Haetaan luokan nimi
        luokka = cursor.fetchone()

        if not luokka:
            # Jos luokkaa ei löydy
            return "Tuntematon luokka"
        
        return luokka['luokka_nimi']

    except mysql.connector.Error as err:
        print(f"Virhe tietokannan kyselyssä: {err}")
        return "Virhe luokan haussa"

    finally:
        cursor.close()
        connection.close()

#päivittää oppilaan ryhmän/luokan
def update_student_class(oppilas_id, luokka_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = "UPDATE oppilas SET luokkaID = %s WHERE oppilasID = %s"
    cursor.execute(query, (luokka_id, oppilas_id))

    connection.commit()
    cursor.close()
    connection.close()


def get_results_by_oppilas_id(oppilas_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = '''
        SELECT pelitulosID, Pelit_peliID, Oppilas_oppilasID, pisteet, kysymys_maara, oikeat_vastaukset, pvm
        FROM pelitulos
        WHERE Oppilas_oppilasID = %s
        ORDER BY pvm DESC
    '''
    cursor.execute(query, (oppilas_id,))
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return results

def get_vastaukset_by_pelitulos_id(pelitulos_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT 
            v.vastausID,
            v.Pelitulos_pelitulosID,
            v.Tehtava_tehtavaID,
            t.kysymys,
            v.pelaajan_vastaus,
            v.pelaajan_vastaus_JSON,
            v.onko_oikein,
            v.aikaleima
        FROM 
            pelaajan_vastaus v
        JOIN 
            tehtava t ON v.Tehtava_tehtavaID = t.tehtavaID
        WHERE 
            v.Pelitulos_pelitulosID = %s;
    """
    cursor.execute(query, (pelitulos_id,))
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return results

get_db_connection()