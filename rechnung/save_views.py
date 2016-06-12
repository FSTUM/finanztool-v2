
def form_rechnung(request, rechnung_id=None):
    rechnung = None
    rechnungform = None
    postenform = None

    #Rechnungsinstanz holen
    if rechnung_id:
        rechnung = get_object_or_404(Rechnung, pk=rechnung_id)

    #Etwas wurde eingegeben in den Forms eingegeben
    if request.method == "POST":

        if 'saverechnung' in request.POST:
            rechnungform = RechnungForm(request.POST, instance=rechnung)

            if rechnungform.is_valid():
                neue_rechnung = rechnungform.save()

                return redirect('rechnung:form_rechnung', rechnung_id=rechnung.pk)

        elif 'saveposten' in request.POST:
            postenform = PostenForm(request.POST, instance=Posten())

            if postenform.is_valid():
                neuer_posten = postenform.save()

                return redirect('rechnung:form_rechnung', rechnung_id=rechnung.pk)

    else:
        rechnungform = RechnungForm(instance=rechnung)
        postenform = PostenForm(instance=Posten())
        return render(request, 'rechnung/form_rechnung.html', {'rechnungform': rechnungform, 'postenform':postenform, 'rechnung':rechnung})



# view schreiben, der die rechnung form anzeigt, und darunter eine tabelle mit allen posten und darunter ein neues posten formular
# form prefix (wenn field name gleich z.b.)
# posten form anpassen, damit sie anzahlposten beinhaltet
# view: formulare speichern, anzahlposten, wenn neu angelegt, zur rechnung hinzufügen
