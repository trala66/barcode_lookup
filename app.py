# app.py (Minimal version til test af databaseforbindelse og miljøvariabler)
import os
from dotenv import load_dotenv
from flask import Flask, render_template_string
import psycopg2

# Vi lader denne stå, selvom den ikke bruges på Railway, for at undgå fejl under lokal test.
load_dotenv() 

app = Flask(__name__)

DB_VARIABLE_NAMES = [
    'DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 
    'DATABASE_PASSWORD', 'DATABASE_PORT', 'DB_SSLMODE'
]

def get_db_config_and_env_status():
    """Henter databasekonfiguration fra miljøvariabler og logger dem."""
    config = {}
    env_status = {}
    
    # Indsaml både konfigurationen og miljøstatus for debug
    for name in DB_VARIABLE_NAMES:
        value = os.environ.get(name)
        env_status[name] = f"'{value}'" if value else "❌ MANGES (eller er tom)"
        if name in ['DATABASE_PORT', 'DB_SSLMODE']:
             config[name] = int(value) if name == 'DATABASE_PORT' and value else value
        else:
             config[name] = value

    return config, env_status

def fetch_first_product(config):
    """Forsøg at oprette forbindelse og hente den første række."""
    connection = None
    result = None
    error = None
    
    try:
        # Tjek om host er sat, da None får psycopg2 til at lede efter en socket
        if not config.get('host'):
             # Returner fejl her, da vi ved, at psycopg2 vil fejle
             raise ValueError("DATABASE_HOST er tom eller mangler.")

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
        error = str(e)
        
    finally:
        if connection:
            connection.close()
            
    return result, error

@app.route('/')
def test_db():
    config, env_status = get_db_config_and_env_status()
    
    # Forsøg kun at hente produktet, hvis hosten findes
    if config.get('host'):
        result, db_error = fetch_first_product(config)
    else:
        result = None
        db_error = "Kan ikke teste database. DATABASE_HOST er tom i miljøet."


    # --- Vis miljøstatus og resultat i HTML ---
    
    env_table = "".join([
        f"<li class='flex justify-between border-b py-2'><span class='font-mono text-gray-600'>{name}</span><span class='font-bold {('text-red-500' if 'MANGES' in status else 'text-green-600')}'>{status}</span></li>" 
        for name, status in env_status.items()
    ])

    if db_error:
        db_result_html = f"<h2 class='text-2xl text-red-600 mb-4'>❌ Databaseforbindelsesfejl</h2><p class='bg-red-100 p-3 rounded text-red-800'>{db_error}</p>"
    elif result:
        db_result_html = f"<h2 class='text-2xl text-green-600 mb-4'>✅ Forbindelse og Forespørgsel Lykkedes</h2><pre class='bg-gray-100 p-3 rounded'>{result}</pre>"
    else:
        db_result_html = f"<h2 class='text-2xl text-yellow-600 mb-4'>⚠️ Database Test Resultat</h2><p class='bg-yellow-100 p-3 rounded text-yellow-800'>{result}</p>"


    html_content = f"""
    <html>
    <head>
        <title>Railway DB Debugger</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 p-8">
        <div class="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-xl">
            <h1 class="text-3xl font-bold mb-6 text-center text-indigo-700">Railway Miljø & Database Debugger</h1>
            
            <div class="mb-8 border p-4 rounded-lg bg-blue-50">
                <h2 class="text-xl font-semibold mb-3 text-blue-700">1. Miljøvariabler Fundet (os.environ.get)</h2>
                <ul class="list-none p-0">{env_table}</ul>
            </div>
            
            <div class="border p-4 rounded-lg bg-white shadow">
                <h2 class="text-xl font-semibold mb-3 text-indigo-700">2. Database Test Resultat</h2>
                {db_result_html}
            </div>
            
            <p class='mt-6 text-sm text-gray-500 text-center'>Konfigurationsdata forsøgt brugt: {config}</p>
        </div>
    </body>
    </html>
    """
        
    return render_template_string(html_content)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
