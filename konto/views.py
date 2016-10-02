from io import TextIOWrapper

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import UploadForm
from .parser import parse_camt_csv


@login_required
def einlesen(request):
    form = UploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        csv_file = request.FILES.get('csv_file')
        csv_file_text = TextIOWrapper(csv_file.file, encoding='iso-8859-1')
        results, errors = parse_camt_csv(csv_file_text)

        print(repr(results))

        context = {'results': results,
                   'errors': errors}
        return render(request, 'konto/mapping.html', context)

    context = {'form': form}
    return render(request, 'konto/einlesen.html', context)
