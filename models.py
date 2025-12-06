import mysql.connector

# ----------------------------------------------------
# MAIN DB CONNECTION FUNCTIONS
# ----------------------------------------------------

def get_users_connection():
    """Return a fresh connection to users_db"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="RootNew!234",
        database="users_db"
    )


def get_pets_connection():
    """Return a fresh connection to pets_db"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="RootNew!234",
        database="pets_db"
    )

import mysql.connector

def get_contact_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="RootNew!234",
        database="contact_us"
    )



# ----------------------------------------------------
# USER FUNCTIONS
# ----------------------------------------------------

def get_user_by_email(email):
    conn = get_users_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user


# ----------------------------------------------------
# CONTACT FORM FUNCTIONS (stored in users_db)
# ----------------------------------------------------

def save_contact_message(name, email, phone, message):
    conn = get_contact_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO contact_messages (name, email, phone, message)
        VALUES (%s, %s, %s, %s)
    """
    values = (name, email, phone, message)

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

import mysql.connector

def get_boarding_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="RootNew!234",
        database="boarding_db"
    )