from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Health_Indicator, Profile
from .upload_reading import UPLOAD_FORMAT_CHOICES, CHOICE_NAME


class HealthIndicatorForm(ModelForm):
    """
    health indicator form (for multichart view)
    """
    class Meta:
        """ """
        model = Health_Indicator
        fields = ['name', 'important']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. \'Poor physical health days\'',
                    'size': 100,
                }
            )
        }


class LoginForm(forms.Form):
    """
    login form for user management

    """
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': "form-control", 'placeholder': "Username"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': "form-control", 'placeholder': "Password"}
        )
    )


# This form needed to get user first and last name and email for creating a new user
# Django default create user form only covers username and password
# Developed by Kim Hawkins
"""param:UserCreationForm: A Django ModelForm for creating a new user"""


class NewUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password1', 'password2',)

# This form ensures Profile model is included when creating a new user: Hawkins
# Choice of user type: administrator or assistant


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # Field class assumes the value is required and will raise a Validation Error exception
        fields = ('utype',)
        # override label else it displays 'utype'
        labels = {'utype': _('User Type'), }


# Not using a ModelForm because this needs to include data for
# both Document and Data_Set model classes - we could make an
# additional Model class (e.g. NewDataUpload entity) with the
# right fields and then create a ModelForm from that, but that
# seems like an extra step.
class UploadNewDataForm(forms.Form):
    """
    Form subclass for displaying an upload form for new data sets.
    """
    file = forms.FileField(
        label='Data File',
        help_text='File containing data in CSV format'
    )

    column_format = forms.ChoiceField(
        label='CSV file format',
        help_text='What columns to use to identify counties in the uploaded CSV file',
        widget=forms.RadioSelect,
        choices=UPLOAD_FORMAT_CHOICES,
        required=True,
        initial=CHOICE_NAME
    )

    # This needs to be required once we have a way to create new ones #
    indicator = forms.ModelChoiceField(
        queryset=Health_Indicator.objects.all(),
        label='Health indicator',
        help_text='The health indicator/metric that this file contains data for',
        required=False
    )

    source = forms.CharField(
        label='Data source',
        help_text='The source/provenance of the data',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )

    # The default value should not be hardcoded!
    year = forms.IntegerField(
        label='Data year',
        help_text='Year this data is from',
        initial=2018,
        min_value=1000,
        max_value=9999
    )

