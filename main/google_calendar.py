from django.shortcuts import redirect, render
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from django.conf import settings
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Настройка клиентских данных OAuth
SCOPES = ['https://www.googleapis.com/auth/calendar']  # Используйте нужные права доступа


def get_google_calendar_service(request):
    # Проверьте, авторизован ли пользователь
    if 'credentials' not in request.session:
        return redirect('google_calendar_init')

    credentials_info = request.session['credentials']

    # Создаем объект Credentials из информации в сессии
    credentials = Credentials(
        token=credentials_info['token'],
        refresh_token=credentials_info['refresh_token'],
        token_uri=credentials_info['token_uri'],
        client_id=credentials_info['client_id'],
        client_secret=credentials_info['client_secret'],
        scopes=credentials_info['scopes']
    )

    # Проверка, нужно ли обновить токен
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_calendar_event(summary, description, start_time, end_time, request):
    service = get_google_calendar_service(request)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event



