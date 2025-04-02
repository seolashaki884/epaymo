from django.shortcuts import render
from .models import Document

def home(request):
    documents = Document.objects.all()  # Fetch all documents
    print(f"Documents in View: {documents.count()}")  # Debugging
    return render(request, 'core/index.html', {'documents': documents})

