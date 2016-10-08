from io import TextIOWrapper

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import UploadForm, MappingConfirmationForm
from .parser import parse_camt_csv

@login_required
def einlesen(request):
    form = UploadForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        csv_file = request.FILES.get('csv_file')
        csv_file_text = TextIOWrapper(csv_file.file, encoding='iso-8859-1')
        results, errors = parse_camt_csv(csv_file_text)

        request.session['results'] = results
        request.session['errors'] = errors
        return redirect('konto:mapping')

    context = {'form': form}
    return render(request, 'konto/einlesen.html', context)

@login_required
def mapping(request):
    try:
        results = request.session['results']
        errors = request.session['errors']
    except KeyError:
        return redirect('konto:einlesen')

    mapping_form = MappingConfirmationForm(request.POST or None,
                                           mappings=results)

    if mapping_form.is_valid():
        mapping_form.save()
        del request.session['results']
        del request.session['errors']

        return redirect('rechnung:index')

    context = {'results': results,
               'errors': errors,
               'form': mapping_form}
    return render(request, 'konto/mapping.html', context)
