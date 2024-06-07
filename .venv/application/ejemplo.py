import flask
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = flask.Flask(__name__)

# Define la URL de redireccionamiento para la autorización
REDIRECT_URI = "http://localhost:5000/oauth2callback"

@app.route('/')
def index():
    # Muestra la página principal con un enlace para iniciar sesión con Google
    return flask.render_template('index.html')

@app.route('/files')
def show_files():
    # Obtiene las credenciales y verifica si están expiradas o no existen
    credentials = get_credentials()
    if credentials is None or credentials.expired:
        print("Credenciales expiradas o no existentes.")
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        print('now calling fetch')
        # Obtener la lista de carpetas y archivos de Google Drive
        folders, files = fetch_folders_and_files()
        
        # Obtener el ID de la última hoja de cálculo abierta y guardarlo en el archivo JSON
        last_spreadsheet_id = flask.request.args.get('spreadsheet_id')
        if last_spreadsheet_id:
            save_last_spreadsheet_id(last_spreadsheet_id)
        
        return flask.render_template('files.html', folders=folders, files=files)

@app.route('/get-files-from-folder', methods=['POST'])
def get_files_from_folder():
    # Obtiene el ID de la carpeta seleccionada
    folder_id = flask.request.form['folder_id']
    if folder_id:
        # Busca las hojas de cálculo en la carpeta seleccionada
        all_files = fetch(f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'", sort='modifiedTime desc')
        return flask.jsonify({'success': True, 'files': all_files})
    else:
        # Busca las hojas de cálculo en la carpeta raíz
        all_files = fetch("'root' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'", sort='modifiedTime desc')
        return flask.jsonify({'success': True, 'files': all_files})

def save_last_spreadsheet_id(spreadsheet_id):
    # Guarda el ID de la última hoja de cálculo abierta en un archivo JSON
    with open('last_spreadsheet_id.json', 'w') as file:
        json.dump({'spreadsheet_id': spreadsheet_id}, file)

def get_last_spreadsheet_id():
    # Obtiene el ID de la última hoja de cálculo abierta desde el archivo JSON
    if os.path.exists('last_spreadsheet_id.json'):
        with open('last_spreadsheet_id.json', 'r') as file:
            data = json.load(file)
        return data.get('spreadsheet_id')
    return None

@app.route('/show-spreadsheet', methods=['POST'])
def show_spreadsheet():
    # Muestra los datos de la hoja de cálculo seleccionada
    spreadsheet_id = flask.request.form['spreadsheet_id']
    if spreadsheet_id:
        data = fetch_spreadsheet_data(spreadsheet_id)
        if data:
            save_last_spreadsheet_id(spreadsheet_id)
            return flask.jsonify({'success': True, 'data': data})
        else:
            return flask.jsonify({'success': False, 'message': 'Error fetching spreadsheet data'})
    else:
        return flask.jsonify({'success': False, 'message': 'Spreadsheet ID not provided'})

@app.route('/save-changes', methods=['POST'])
def save_changes():
    # Guarda los cambios realizados en la hoja de cálculo
    spreadsheet_id = flask.request.json['spreadsheet_id']
    values = flask.request.json['values']
    if spreadsheet_id and values:
        success = update_spreadsheet_values(spreadsheet_id, values)
        if success:
            save_last_spreadsheet_id(spreadsheet_id)
            return flask.jsonify({'success': True})
        else:
            return flask.jsonify({'success': False, 'message': 'Error saving changes to spreadsheet'})
    else:
        return flask.jsonify({'success': False, 'message': 'Spreadsheet ID or values not provided'})

@app.route('/oauth2callback')
def oauth2callback():
    # Maneja el flujo de OAuth2 para autenticarse con Google
    flow = Flow.from_client_secrets_file(
        'client_id.json',
        scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'],
        redirect_uri=REDIRECT_URI
    )
    flow.include_granted_scopes = True
    if 'code' not in flask.request.args:
        # Inicia el flujo de autenticación
        print("Iniciando flujo de autenticación.")
        auth_uri, _ = flow.authorization_url(prompt='consent')
        return flask.redirect(auth_uri)
    else:
        # Completa el flujo de autenticación y obtiene las credenciales
        auth_code = flask.request.args.get('code')
        print("Recibido código de autorización:", auth_code)
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        save_credentials(credentials)
        print("Credenciales guardadas exitosamente.")
        
        # Verifica si las credenciales son válidas
        if credentials.valid:
            print("Credenciales válidas. Redireccionando a tus archivos.")
            return flask.redirect(flask.url_for('show_files'))
        else:
            print("Las credenciales no son válidas. Reintentando la autorización.")
            return flask.redirect(flask.url_for('oauth2callback'))

def get_credentials():
    # Obtiene las credenciales desde el archivo JSON o retorna None si no existen
    if not flask.session.get('is_guest', False):  # Si no es un usuario invitado
        if os.path.exists('token.json') and os.path.getsize('token.json') > 0:
            print("Cargando credenciales existentes.")
            with open('token.json', 'r') as token_file:
                token_data = json.load(token_file)
            credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data['refresh_token'],
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )
            return credentials if not credentials.expired else None
        print("No se encontró ningún archivo de credenciales existente o está vacío.")
    else:
        print("Modo invitado. No se necesitan credenciales para acceder a los servicios de Google.")
    return None

def save_credentials(credentials):
    # Guarda las credenciales en un archivo JSON
    credentials_dict = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    with open('token.json', 'w') as token_file:
        json.dump(credentials_dict, token_file)
    print("Credenciales guardadas correctamente.")

def fetch_spreadsheet_data(spreadsheet_id):
    # Obtiene los datos de la hoja de cálculo especificada
    if not flask.session.get('is_guest', False):  # Verificar si es un usuario invitado
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='A1:Z100').execute()
        values = result.get('values', [])
        return values
    else:
        return None

def update_spreadsheet_values(spreadsheet_id, values):
    # Actualiza los valores de la hoja de cálculo especificada
    if not flask.session.get('is_guest', False):  # Verificar si es un usuario invitado
        credentials = get_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        body = {'values': values}
        result = service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range='A1:Z100', valueInputOption='USER_ENTERED', body=body).execute()
        return True
    else:
        return False  # Devolver False para indicar que la actualización no se realizó

@app.route('/logout')
def logout():
    # Elimina las credenciales guardadas y redirige a la página principal
    if os.path.exists('token.json'):
        os.remove('token.json')
        print("Credenciales eliminadas.")
    return flask.redirect(flask.url_for('index'))

def fetch_folders_and_files():
    # Obtiene la lista de carpetas y archivos de Google Drive
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    folders = fetch("mimeType = 'application/vnd.google-apps.folder'")
    files = fetch("'root' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'", sort='modifiedTime desc')
    return folders, files

def fetch(query, sort='modifiedTime desc'):
    # Ejecuta una consulta en Google Drive y retorna los resultados
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    results = service.files().list(
        q=query, orderBy=sort, pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items

@app.route('/search-data', methods=['POST'])
def search_data():
    # Busca datos en la hoja de cálculo basándose en los parámetros de búsqueda
    spreadsheet_id = flask.request.json['spreadsheet_id']
    search_column = flask.request.json['search_column']
    search_value = flask.request.json['search_value']
    
    if not flask.session.get('is_guest', False):  # Verificar si es un usuario invitado
        if spreadsheet_id and search_column and search_value:
            data = fetch_spreadsheet_data(spreadsheet_id)
            if data:
                filtered_data = [row for row in data if len(row) > search_column and row[search_column] == search_value]
                return flask.jsonify({'success': True, 'data': filtered_data})
            else:
                return flask.jsonify({'success': False, 'message': 'Error fetching spreadsheet data'})
        else:
            return flask.jsonify({'success': False, 'message': 'Spreadsheet ID, search column, or search value not provided'})
    else:
        return flask.jsonify({'success': False, 'message': 'Guest mode does not support data search.'})

if __name__ == '__main__':
    # Establece la clave secreta para la sesión Flask
    app.secret_key = os.urandom(24)
    app.run(debug=True)
