from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
import os
from datetime import timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

app = Flask(__name__)
app.secret_key = 'random secret'
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='264663196120-o8kgfd87r2o4sdniljd14v8lvchtu4nj.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'https://www.googleapis.com/auth/drive.metadata.readonly',  # Cambiado al alcance necesario
        'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs',
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDS_FILENAME = 'credentials.json'
DRIVE_API_VERSION = 'v3'

def get_drive_service():
    creds = None
    if 'credentials' in session:
        creds = Credentials.from_authorized_user_info(session['credentials'])
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDS_FILENAME, SCOPES)
        creds = flow.run_local_server(port=0)
    session['credentials'] = creds.to_json()
    return build('drive', DRIVE_API_VERSION, credentials=creds)

@app.route('/')
def home():
    if 'credentials' in session:
        return redirect(url_for('logeado'))
    else:
        return redirect(url_for('authorize'))

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/logeado')
def logeado():
    drive_service = get_drive_service()
    if 'credentials' not in session:
        return redirect(url_for('authorize'))
    else:
        files = drive_service.files().list(pageSize=10).execute().get('files', [])
        return render_template('logeado.html', email=session.get('email'), files=files)

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('credentials', None)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload():
    drive_service = get_drive_service()
    file_id = request.form['file_id']
    file_metadata = drive_service.files().get(fileId=file_id).execute()
    file_name = file_metadata['name']
    return f'Archivo cargado: {file_name}'

if __name__ == '__main__':
    app.run(debug=True)
