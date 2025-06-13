from django.shortcuts import render

def dashbord(request):
    return render(request, 'account/dashbord.html')

def subscribe(request):
    return render(request, 'account/subscribe.html')

def castomer_request(request):
    return render(request, 'account/castomer_request.html')

def castomer_mail(request):
    return render(request, 'account/castomer_mail.html')

def customer_calculation(request):
    return render(request, 'account/customer_calculation.html')

def payment(request):
    return render(request, 'account/payment.html')