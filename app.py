# db_test_app.py (Minimal version til test af databaseforbindelse)
import os
from dotenv import load_dotenv
from flask import Flask, render_template_string
import psycopg2

# Indlæs miljøvariabler (til lokal test)
# load_dotenv()

app = Flask(__name__)

# Database konfiguration
def get_db_config():
    """Henter databasekonfiguration fra miljøvariabler og logger dem."""
    config = {
        'host': os.environ.get('DATABASE_HOST'),
        'database': os.environ.get('DATABASE_NAME'),
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD'),
        'port': int(os.environ.get('DATABASE_PORT', '10342')),
        'sslmode': os.environ.get('DB_SSLMODE', 'require')
    }
    
    # Simpel maskering af password til logging
    def _mask(s, keep=2):
        return s[:keep] + "..." if s and len(s) > keep else "..."
        
    print(
        "DB params -> host=", config.get('host'),
        " db=", config.get('database'),
        " user=", config.get('user'),
        " port=", config.get('port'),
        " sslmode=", config.get('sslmode'),
        " pwd=", _mask(config.get('password', ''))
    )
    return config

def fetch_first_product():
    """Forsøg at oprette forbindelse og hente den første række."""
    config = get_db_config()
    connection = None
    result = None
    error = None
    
    try:
        # Tjek om host er sat, da None får psycopg2 til at lede efter en socket
        if not config.get('host'):
             raise ValueError(f"DATABASE_HOST er tom eller mangler. Værdier: {config}")

        connection = psycopg2.connect(**config)
        
        with connection.cursor() as cursor:
            # Hent de første 5 kolonner og 1 række til test
            cursor.execute("SELECT * FROM products LIMIT 1;")
            row = cursor.fetchone()
            col_names = [desc[0] for desc in cursor.description]
            
            if row:
                result = dict(zip(col_names, row))
            else:
                result = "Tabellen 'products' er tom."
                
    except Exception as e:
        error = f"Databaseforbindelsesfejl: {e}. Forsøgte at forbinde med konfiguration: {config}"
        
    finally:
        if connection:
            connection.close()
            
    return result, error

@app.route('/')
def test_db():
    result, error = fetch_first_product()

    if error:
        # Brug en enkel HTML-streng til at vise fejl
        html_content = f"""
        <html><body>
        <h1 style='color: red;'>❌ Database Fejl</h1>
        <pre>{error}</pre>
        <p>Tjek venligst loggen for at sikre, at DATABASE_HOST er sat korrekt.</p>
        </body></html>
        """
    else:
        # Brug en enkel HTML-streng til at vise succes/resultat
        html_content = f"""
        <html><body>
        <h1 style='color: green;'>✅ Database Forbindelse Virker</h1>
        <h2>Første post i 'products':</h2>
        <pre>{result}</pre>
        </body></html>
        """
        
    return render_template_string(html_content)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)