
import os
from dotenv import load_dotenv
from flask import Flask, request, render_template
import psycopg2
import sys

# --- Initialisering ---

# Indlæs miljøvariabler (til lokal test)
load_dotenv()

app = Flask(__name__)

# Database konfiguration
def get_db_config():
    """Henter databasekonfiguration fra miljøvariabler."""
    return {
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME'),
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'port': int(os.environ.get('DATABASE_PORT', '10342')),
        'sslmode': os.environ.get('DB_SSLMODE', 'require')
    }

# --- Database Funktioner ---

def connect_to_database():
    """Opretter forbindelse til PostgreSQL databasen."""
    config = get_db_config()
    
    # Simpel maskering af password til logging
    def _mask(s, keep=2):
        return s[:keep] + "..." if s and len(s) > keep else "..."

    '''    
    print(
        "DB params -> host=", config.get('host'),
        " db=", config.get('database'),
        " user=", config.get('user'),
        " port=", config.get('port'),
        " sslmode=", config.get('sslmode'),
        " pwd=", _mask(config.get('password', ''))
    )
    '''

    try:
        connection = psycopg2.connect(**config)
        print("Forbindelse til database oprettet succesfuldt")
        return connection
    except Exception as e:
        print(f"Fejl ved oprettelse af databaseforbindelse: {e}")
        return None

def get_product_info(barcode):
    """Henter produktinformation baseret på stregkoden fra databasen."""
    connection = connect_to_database()
    if not connection:
        return {'error': "Kunne ikke oprette forbindelse til databasen.", 'barcode': barcode}
    
    product_info = None
    try:
        with connection.cursor() as cursor:
            # SQL forespørgsel til at finde produkt baseret på stregkode
            query = """
            SELECT product_id, description, unitprice, quantity 
            FROM products 
            WHERE barcode = %s
            """
            cursor.execute(query, (barcode,))
            result = cursor.fetchone()
            
            if result:
                product_id, description, unitprice, quantity = result
                product_info = {
                    'product_id': product_id,
                    'description': description,
                    'unitprice': f"{unitprice} kr.",
                    'quantity': quantity,
                    'barcode': barcode
                }
            else:
                product_info = {'error': f"Produkt ikke fundet i databasen.", 'barcode': barcode}
                
    except Exception as e:
        print(f"Fejl ved databaseforespørgsel: {e}")
        product_info = {'error': f"Databasefejl under forespørgsel: {e}", 'barcode': barcode}
    finally:
        connection.close()
    
    return product_info

# --- Flask Ruter ---

@app.route('/', methods=['GET', 'POST'])
def barcode_lookup():
    """
    Håndterer både visning af formularen (GET) og opslag (POST).
    """
    result = None
    error = None
    barcode = ""

    if request.method == 'POST':
        # Forsøg at hente stregkoden fra formulardata
        barcode = request.form.get('barcode').strip()
        
        if barcode:
            # Udfør databaseopslag
            product_info = get_product_info(barcode)
            
            if 'error' in product_info:
                error = product_info['error']
            else:
                result = product_info
        else:
            error = "Indtast venligst en stregkode."
            
    # Render skabelonen med resultater/fejl, hvis de eksisterer
    return render_template('index.html', result=result, error=error, current_barcode=barcode)

# --- Deployment ---

if __name__ == '__main__':
    # Brug miljøvariabel for porten, hvilket er nødvendigt for Railway
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
