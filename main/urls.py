from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
path('register', views.register_site, name='register_site'),
    path('register/', views.register, name='register'),
path('login/', views.login, name='login'),
path('login', views.loginsystem, name='login_method'),
path('notes/', views.notes, name='notes'),
    path('logout',views.logout, name='logout'),
path('note/',views.note, name='note'),
path('notes/<int:note_id>',views.go_note, name='go_note'),
path('new_note/',views.new_note, name='new_note'),
path('save',views.save, name='save'),
path('delete/<int:note_id>',views.delete, name='delete'),
path('settings/',views.setting, name='settings'),
path('authorize/', views.google_calendar_init, name='google_calendar_init'),
    path('oauth2callback/', views.google_calendar_redirect, name='google_calendar_redirect'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('add_task', views.add_task, name='add_task'),
path('tasks/', views.return_task, name='tasks'),
path('update_server/', views.webhook, name='update_server'),

]