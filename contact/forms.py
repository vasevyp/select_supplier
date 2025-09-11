# contacts/forms.py
from django import forms
from .models import ContactMessage
from captcha.fields import CaptchaField

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    # captcha = forms.CharField(label='Введите 123', required=True)
    captcha = CaptchaField()
    
    # def clean_captcha(self):
    #     data = self.cleaned_data['captcha']
    #     if data != '123':
    #         raise forms.ValidationError("Неверный код")
    #     return data    