import os
import flask
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = flask.Flask(__name__)

# Define la URL de redireccionamiento para la autorización
REDIRECT_URI = "http://localhost:5000/oauth2callback"

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/files')
def show_files():
    credentials = get_credentials()
    if credentials is None or credentials.expired:
        print("Credenciales expiradas o no existentes.")
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        print('now calling fetch')
        all_files = fetch("'root' in parents and mimeType = 'application/vnd.google-apps.spreadsheet'", sort='modifiedTime desc')
        return flask.render_template('files.html', files=all_files)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        'client_id.json',
        scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets'],
        redirect_uri=REDIRECT_URI
    )
    flow.include_granted_scopes = True
    if 'code' not in flask.request.args:
        print("Iniciando flujo de autenticación.")
        auth_uri, _ = flow.authorization_url(prompt='consent')
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        print("Recibido código de autorización:", auth_code)
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        save_credentials(credentials)
        print("Credenciales guardadas exitosamente.")
        
        # Verificar si las credenciales guardadas son válidas
        if credentials.valid:
            print("Credenciales válidas. Redireccionando a tus archivos.")
            return flask.redirect(flask.url_for('show_files'))
        else:
            print("Las credenciales no son válidas. Reintentando la autorización.")
            return flask.redirect(flask.url_for('oauth2callback'))

def get_credentials():
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
    return None

import json

def save_credentials(credentials):
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

@app.route('/logout')
def logout():
    if os.path.exists('token.json'):
        os.remove('token.json')
        print("Credenciales eliminadas.")
    return flask.redirect(flask.url_for('index'))


def fetch(query, sort='modifiedTime desc'):
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    results = service.files().list(
        q=query, orderBy=sort, pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items

if __name__ == '__main__':
    if os.path.exists('client_id.json') == False:
        print('Client secrets file (client_id.json) not found in the app path.')
        exit()
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.run(debug=True)
