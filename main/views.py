import datetime
import json
from pytz import timezone, UnknownTimeZoneError
from django.utils.timezone import now as django_now
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .models import Note, Users, Tasks


#главная страница
def main(request):
    # Получение часового пояса из GET-запроса
    user_timezone = request.GET.get('timezone', 'UTC')  # По умолчанию 'UTC'
    try:
        # Устанавливаем часовой пояс пользователя
        user_time = django_now().astimezone(timezone(user_timezone))
    except UnknownTimeZoneError:
        # Если часовой пояс некорректный, используем UTC
        user_time = django_now()
    # Определяем время суток
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


#страница регистрации
def register_site(request):
    return render(request, 'main/register.html')

#регистрация-метод
def register(request):
    login = request.POST.get("login", "Undefined")
    password_1 = request.POST.get("password1", 1)
    password_2 = request.POST.get("password2", 1)
    all_users = db()
    exist = False
    for i in range(len(all_users)):
        if login == all_users[i][0]:  # логины
            exist = True
            break
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
        Users.objects.create(login=login, password=password_1 )
        settings.MY_GLOBAL_VARIABLE = login
        return redirect('main')

    return render(request, 'main/register.html', {"message": message, "message_class": message_class})

#обращение к бд
def db():
    return Users.objects.values_list('login', 'password')

#страница входа
def login(request):
    return render(request, 'main/login.html')

#обработка входа
def loginsystem(request):
    login = request.POST.get("login", "Undefined")
    password_1 = request.POST.get("password", 1)
    all_users = db()
    exist = Users.objects.filter(login=login).exists()
    if exist == True:
        user = Users.objects.get(login=login)
        password = user.password
    if exist==False:
        mess_class = "error"
        mess = "Пользователя не существует"
    elif password_1 != password:
        mess_class = "err"
        mess = "Неверный пароль"
    else:
        mess = "Успешно!"
        mess_class = "succ"
        settings.MY_GLOBAL_VARIABLE = login
        return redirect('main')

    return render(request, 'main/login.html', {"mess": mess, "mess_class": mess_class})

#обработка выхода
def logout(request):
    settings.MY_GLOBAL_VARIABLE = "Undefined"
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)

#страница настроек
def setting(request):
    return render(request, 'main/settings.html')

def return_task(request):
    tasks = Tasks.objects.filter(login=settings.MY_GLOBAL_VARIABLE).values('text')
    return {"tasks" : tasks}

def add_task(request):
   text = request.POST.get("taskName", "Undefined")
   if text != "Undefined" and text != "":
    Tasks.objects.create(login=settings.MY_GLOBAL_VARIABLE, text = text)
   referer = request.META.get('HTTP_REFERER', '/')
   return redirect(referer)

#метод выводящий заметки
def return_notes(request):
    notes = Note.objects.filter(login=settings.MY_GLOBAL_VARIABLE).order_by('-id').values('id', 'text')
    count = len(notes)
    shortnotes = []
    for note in notes:
        text = note['text'][:57] + "..." if len(note['text']) > 57 else note['text']
        if text != "":
            shortnotes.append({'id': note['id'], 'text': text})

    return {"count": count, "shortnotes": shortnotes}

#полная заметка - общий шаблон страницы
def note(request):
    return render(request, 'main/note.html')

def save(request):
    note_text = request.POST.get("note_text", "")
    note_id = request.POST.get("note_id", None)
    if note_text == "":
        try:
            empty_note = Note.objects.filter(id=note_id)
            empty_note.delete()
        except Exception as e:
            pass
    elif note_id:  # Проверяем, что ID передан
        try:
            Note.objects.filter(id=note_id).update(text=note_text)
        except Exception as e:
            print(f"Ошибка при обновлении заметки: {e}")

    return redirect('notes')


def new_note(request):
    try:
        this_note = Note.objects.create(login=settings.MY_GLOBAL_VARIABLE, text='')
        note_id = this_note.id
    except:
       print("Ошибка при создании заметки")
    return render(request, 'main/new_note.html',{"note_id" : note_id, "current_login" : settings.MY_GLOBAL_VARIABLE})

def go_note(request, note_id=None):
    if not note_id:
        return redirect('notes')  # Перенаправить на список заметок
    this_note = get_object_or_404(Note, id=note_id)
    return render(request, 'main/note_detail.html', {'note': this_note, 'note_id':note_id, "current_login" : settings.MY_GLOBAL_VARIABLE})

def delete(request, note_id=None):
    this_note = get_object_or_404(Note, id=note_id)
    deleted_note= Note.objects.get(id=note_id)
    deleted_note.delete()

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)

def notes(request):
    context1= {"current_login" : settings.MY_GLOBAL_VARIABLE}
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

    # Сохраняем токены в сессии
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

    # Проверяем и обновляем токен, если он истёк
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    service = build('calendar', 'v3', credentials=credentials)

    # Получаем события
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Подготовка данных для передачи в шаблон
    event_list = []
    for event in events:
        event_list.append({
            'summary': event.get('summary', 'No Title'),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date'))
        })

    return render(request, 'main/calendar.html', {'events': json.dumps(event_list)})



