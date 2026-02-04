from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    # Query all tasks from the database
    queryset = Task.objects.all()
    # Use the serializer we just created to translate them
    serializer_class = TaskSerializer