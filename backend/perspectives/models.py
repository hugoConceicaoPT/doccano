from django.db import models
from projects.models import Member, Project 

class Perspective(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    questions = models.JSONField(default=list)
    answers = models.JSONField(default=list)
    member = models.ForeignKey(to=Member, on_delete=models.CASCADE)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)