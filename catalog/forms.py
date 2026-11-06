from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Book, ContactMessage

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Elektron pochta')
    group_name = forms.CharField(required=False, label='Guruh/sinf')
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'group_name')
        labels = {'username':'Login', 'first_name':'Ism', 'last_name':'Familiya'}

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title','author','subject','category','description','language','published_year','isbn','cover','pdf_file','external_url')
        labels = {'title':'Kitob nomi','author':'Muallif','subject':'Fan','category':'Kategoriya','description':'Qisqacha tavsif','language':'Til','published_year':'Nashr yili','isbn':'ISBN','cover':'Muqova rasmi','pdf_file':'PDF fayl (25 MB gacha)','external_url':'Tashqi havola (ixtiyoriy)'}
        widgets = {'description':forms.Textarea(attrs={'rows':4})}
    def clean_pdf_file(self):
        f = self.cleaned_data.get('pdf_file')
        if f and f.size > 25 * 1024 * 1024: raise forms.ValidationError('PDF hajmi 25 MB dan oshmasligi kerak.')
        if f and f.content_type not in ('application/pdf', 'application/octet-stream'): raise forms.ValidationError('Faqat PDF fayl yuklash mumkin.')
        if f:
            header = f.read(5); f.seek(0)
            if header != b'%PDF-': raise forms.ValidationError('Fayl haqiqiy PDF formatida emas.')
        return f

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name','email','message')
        labels = {'name':'Ism-familiya','email':'Elektron pochta','message':'Murojaat matni'}
        widgets = {'message':forms.Textarea(attrs={'rows':5})}
