from django.shortcuts import render, redirect


def index(request):
    return redirect('admin/')  # render(request, 'index.html', )
