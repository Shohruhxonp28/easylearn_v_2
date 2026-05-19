from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Student


class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, required=True, label='Full Name')
    school = forms.CharField(max_length=200, required=False, label='School')
    group = forms.CharField(max_length=100, required=False, label='Group/Class')
    email = forms.EmailField(required=False)

    class Meta:
        model = Student
        fields = ('username', 'full_name', 'school', 'group', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('full_name', 'school', 'group', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
