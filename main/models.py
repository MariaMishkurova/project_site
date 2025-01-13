#from django.conf import settings
from django.db import models

class Note(models.Model):
    text= models.TextField()
    auto_now_add=True
    login=models.TextField()

def __str__(self):
   return self.text[:50]

class Users(models.Model):
    login= models.TextField()
    password=models.TextField()

class Tasks(models.Model):
    text = models.TextField()
    login = models.TextField()