'''contacts/views.py Обрабатывает отправку контактной формы и отображает страницу контактов'''
from django.core.mail import send_mail
from django.views.generic import TemplateView
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import ContactForm





def contact_view(request):
    '''Обрабатывает POST-запросы для сохранения сообщений контактов и отправки уведомлений 
        по электронной почте. Отображает контактную форму для GET-запросов.'''
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():            
            # Сохраняем сообщение в базу
            message = form.save()
            
            # Отправка email
            subject = f"Новое сообщение: {message.subject}"
            body = f"""
                От: {message.name} <{message.email}>
                Тема: {message.subject}
                Сообщение:
                {message.message}
            """
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_ADMIN],
                fail_silently=False,
            )
            return redirect('contact_success')
    else:
        form = ContactForm()
    
    return render(request, 'contact/contact.html', {'form': form})

class ContactSuccessView(TemplateView):
    template_name = 'contact/contact_success.html'