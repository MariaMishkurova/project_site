import datetime
import json
import pymysql
from pytz import timezone, UnknownTimeZoneError
from django.utils.timezone import now as django_now
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import git


# Подключение к MySQL
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',  # Ваш MySQL пользователь
        password='password',  # Ваш пароль MySQL
        database='your_database'  # Название вашей базы данных
    )
    return connection


def webhook(request):
    if request.method == 'POST':
        repo = git.Repo('MariaMishkurova/project_site')
        origin = repo.remotes.origin
        origin.pull()
        return 'Updated PythonAnywhere successfully', 200
    else:
        return 'Wrong event type', 400


def main(request):
    user_timezone = request.GET.get('timezone', 'UTC')  # По умолчанию 'UTC'
    try:
        user_time = django_now().astimezone(timezone(user_timezone))
    except UnknownTimeZoneError:
        user_time = django_now()

    current_hour = user_time.hour
    if 6 < current_hour < 13:
        current_time = "Утро"
    elif 13 <= current_hour < 18:
        current_time = "День"
    else:
        current_time = "Вечер"

    context = {
        "current_login": settings.MY_GLOBAL_VARIABLE,
        "current_time": current_time
    }
    context.update(return_task(request))
    return render(request, 'main/main.html', context)


def register_site(request):
    return render(request, 'main/register.html')


def register(request):
    login = request.POST.get("login", "Undefined")
    password_1 = request.POST.get("password1", 1)
    password_2 = request.POST.get("password2", 1)

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT login FROM users WHERE login = %s", (login,))
    all_users = cursor.fetchall()
    connection.close()

    exist = False
    if all_users:
        exist = True

    if exist:
        message_class = "error"
        message = "Пользователь уже существует"
    elif len(login) < 4:
        message_class = "error"
        message = "Логин должен содержать минимум 4 символа"
    elif password_1 != password_2:
        message_class = "error"
        message = "Пароли не совпадают"
    elif len(password_1) < 4:
        message_class = "error"
        message = "Пароль должен содержать минимум 4 символа"
    else:
        message = "Успешно!"
        message_class = "success"

        # Создание нового пользователя в базе данных
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (login, password) VALUES (%s, %s)", (login, password_1))
        connection.commit()
        connection.close()

        settings.MY_GLOBAL_VARIABLE = login
        return redirect('main')

    return render(request, 'main/register.html', {"message": message, "message_class": message_class})


def db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT login, password FROM users")
    all_users = cursor.fetchall()
    connection.close()
    return all_users


def login(request):
    return render(request, 'main/login.html')


def loginsystem(request):
    login = request.POST.get("login", "Undefined")
    password_1 = request.POST.get("password", 1)

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT password FROM users WHERE login = %s", (login,))
    user = cursor.fetchone()
    connection.close()

    if user:
        password = user[0]
    else:
        mess_class = "error"
        mess = "Пользователя не существует"
    if password_1 != password:
        mess_class = "err"
        mess = "Неверный пароль"
    else:
        mess = "Успешно!"
        mess_class = "succ"
        settings.MY_GLOBAL_VARIABLE = login
        return redirect('main')

    return render(request, 'main/login.html', {"mess": mess, "mess_class": mess_class})


def logout(request):
    settings.MY_GLOBAL_VARIABLE = "Undefined"
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def setting(request):
    return render(request, 'main/settings.html')


def return_task(request):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT text FROM tasks WHERE login = %s", (settings.MY_GLOBAL_VARIABLE,))
    tasks = cursor.fetchall()
    connection.close()
    return {"tasks": tasks}


def add_task(request):
    text = request.POST.get("taskName", "Undefined")
    if text != "Undefined" and text != "":
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO tasks (login, text) VALUES (%s, %s)", (settings.MY_GLOBAL_VARIABLE, text))
        connection.commit()
        connection.close()

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def return_notes(request):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, text FROM notes WHERE login = %s ORDER BY id DESC", (settings.MY_GLOBAL_VARIABLE,))
    notes = cursor.fetchall()
    connection.close()

    count = len(notes)
    shortnotes = []
    for note in notes:
        text = note[1][:57] + "..." if len(note[1]) > 57 else note[1]
        if text != "":
            shortnotes.append({'id': note[0], 'text': text})

    return {"count": count, "shortnotes": shortnotes}


def note(request):
    return render(request, 'main/note.html')


def save(request):
    note_text = request.POST.get("note_text", "")
    note_id = request.POST.get("note_id", None)
    if note_text == "":
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            connection.commit()
            connection.close()
        except Exception as e:
            pass
    elif note_id:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE notes SET text = %s WHERE id = %s", (note_text, note_id))
            connection.commit()
            connection.close()
        except Exception as e:
            print(f"Ошибка при обновлении заметки: {e}")

    return redirect('notes')


def new_note(request):
    # Создание новой заметки в базе данных
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO notes (login, text) VALUES (%s, %s)", (settings.MY_GLOBAL_VARIABLE, ''))
        connection.commit()

        # Получение ID только что созданной заметки
        note_id = cursor.lastrowid
        connection.close()
    except Exception as e:
        print(f"Ошибка при создании заметки: {e}")
        note_id = None  # В случае ошибки установим note_id как None

    # Передаем note_id в шаблон
    return render(request, 'main/new_note.html', {"note_id": note_id, "current_login": settings.MY_GLOBAL_VARIABLE})


def go_note(request, note_id=None):
    if not note_id:
        return redirect('notes')  # Перенаправить на список заметок

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
    this_note = cursor.fetchone()
    connection.close()

    return render(request, 'main/note_detail.html',
                  {'note': this_note, 'note_id': note_id, "current_login": settings.MY_GLOBAL_VARIABLE})


def delete(request, note_id=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    connection.commit()
    connection.close()

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def notes(request):
    context1 = {"current_login": settings.MY_GLOBAL_VARIABLE}
    context1.update(return_notes(request))
    return render(request, 'main/notes.html', context1)


def google_calendar_init(request):
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.GOOGLE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=request.build_absolute_uri('/oauth2callback')
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    request.session['state'] = state
    return redirect(authorization_url)


def google_calendar_redirect(request):
    state = request.session.get('state')
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.GOOGLE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/calendar'],
        state=state,
        redirect_uri=request.build_absolute_uri('/oauth2callback')
    )
    flow.fetch_token(authorization_response=request.get_full_path())
    credentials = flow.credentials

    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect('calendar_view')


def calendar_view(request):
    if 'credentials' not in request.session:
        return redirect('google_calendar_init')

    credentials_info = request.session['credentials']
    credentials = Credentials(
        token=credentials_info['token'],
        refresh_token=credentials_info['refresh_token'],
        token_uri=credentials_info['token_uri'],
        client_id=credentials_info['client_id'],
        client_secret=credentials_info['client_secret'],
        scopes=credentials_info['scopes']
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    event_list = []
    for event in events:
        event_list.append({
            'summary': event.get('summary', 'No Title'),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date'))
        })

    return render(request, 'main/calendar.html', {'events': json.dumps(event_list)})
