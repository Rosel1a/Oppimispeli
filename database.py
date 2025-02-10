#Tänne luultavasti sit se SQL-tietokantayhteys
#Tässä saagan epic sql testaus JA SE TOIMII?

import mysql.connector

# Yhdistä MySQL-tietokantaan
db_connection = mysql.connector.connect(
    host="localhost",  # MySQL-palvelimen isäntä (usein 'localhost')
    user="root",       # Käyttäjänimi (muuta tarpeen mukaan)
    password="Salasana1",  # MySQL:n salasana
    database="oppimispeli"   # Tietokannan nimi
)

# Luo kursori, jolla voidaan suorittaa SQL-kyselyt
cursor = db_connection.cursor()

# Esimerkki: Suoritetaan SQL-kysely ja haetaan tietoa
cursor.execute("SHOW TABLES")

# Tulostetaan taulujen nimet
print("Taulut tietokannassa:")
for table in cursor.fetchall():
    print(table[0])  # Tulostetaan taulun nimi

'''
add_user_query = """
    INSERT INTO User (nimi, kayttajanimi, sahkoposti, salasana, syntymapaiva, rooli)
    VALUES (%s, %s, %s, %s, %s, %s)
"""
user_data = ("Testi Käyttäjä", "testikayttaja", "testi@example.com", "salasana123", "2000-01-01", "oppilas")

# Suoritetaan lisäys
cursor.execute(add_user_query, user_data)

# Varmistetaan muutokset
db_connection.commit()

'''

# Tarkistetaan, että käyttäjä on lisätty
cursor.execute("SELECT * FROM User WHERE kayttajanimi = 'testikayttaja'")
print("Lisätty käyttäjä:")
for row in cursor.fetchall():
    print(row)

# Sulje yhteys ja kursori
cursor.close()
db_connection.close()