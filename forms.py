from django import (
    forms
)
from .models import (
    BulkImport,
    Shoe,
    ShoeImage,
    Brand,
    Model,
    Foot,
    Size,
    UserProfile
)
from allauth.account.forms import (
    SignupForm
)
from dal import (
    autocomplete
)
from django.contrib.auth.models import (
    User
)
from django.utils.translation import (
    gettext_lazy as _
)
from captcha.fields import (
    ReCaptchaField
)
from captcha.widgets import (
    ReCaptchaV3
)
from .utils import (
    send_confirm_subscription_email,
)
import requests


class CustomSignupForm(SignupForm):
    subscribed = forms.BooleanField(
        required=False,
        label="Subscribe to SOLESTAR's newsletter."
    )

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        profile = UserProfile.objects.create(user=user)
        # profile.subscribed = self.cleaned_data['subscribed']
        profile.save()
        user.save()
        return user


class BulkInput(forms.ModelForm):
    class Meta:
        model = BulkImport
        fields = ('file',)


class FootForm(forms.ModelForm):
    # captcha = ReCaptchaField(
    #     widget=ReCaptchaV3(
    #     attrs={
    #         'required_score':0.85
    #     }
    # ))

    class Meta:
        model = Foot
        fields = (
            # 'captcha',
            # 'session_id',
            'user',
            'length',
            'width',
            'circumference',
        )


class ShoeImageForm(forms.ModelForm):
    class Meta:
        model = ShoeImage
        fields = (
            'brand',
            'model',
            'color',
            'angle',
            'image'
        )
        widgets = {
            # 'color': autocomplete.ModelSelect2(url='shoe-color-autocomplete')
        }

class ShoeForm(forms.ModelForm):
    class Meta:
        model = Shoe
        fields = (
            'model',
            'size',
            'length',
            'width',
            'circumference',
            'min_foot_length',
            'max_foot_length',
            'min_foot_width',
            'max_foot_width',
            'weight',
            'material_thickness_inner',
            'material_thickness_outer',
            'width_wt',
            'added_by',
            'remeasure',
            'active'
        )
        widgets = {
            'model': autocomplete.ModelSelect2(url='model_autocomplete', attrs={'data-placeholder': 'Enter a brand name...'}),
            'image': forms.ClearableFileInput(attrs={'multiple':True}),
            'length': forms.NumberInput(attrs={'min': 0, 'max': 99, 'placeholder': 'cm'}),
            'width': forms.NumberInput(attrs={'min': 0, 'max': 99, 'placeholder': 'cm'}),
            'circumference': forms.NumberInput(attrs={'min': 0, 'max': 99, 'placeholder': 'cm'}),
            'weight': forms.NumberInput(attrs={'min': 0, 'max': 999, 'placeholder': 'g'}),
            'material_thickness_inner': forms.NumberInput(attrs={'min': 0, 'max': 999, 'placeholder': 'cm'}),
            'material_thickness_outer': forms.NumberInput(attrs={'min': 0, 'max': 999, 'placeholder': 'cm'}),
            # 'added_by': forms.HiddenInput(),
            # 'prices': forms.NumberInput(attrs={'min': 0, 'max': 99999, 'placeholder': '$'}),
        }


class RegisterForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Your email'}),
    )
    subscribe = forms.BooleanField(
        required=False,
        label="Subscribe to SOLESTAR's newsletter."
    )


class DeleteUserForm(forms.Form):
  delete = forms.BooleanField(
    required=True,
    label="Confirm that you want to delete your account:"
  )

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)


class CustomUserForm(forms.Form):
    first_name = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    subscribed = forms.BooleanField(
        required=False,
        label="Subscribe to SOLESTAR's newsletter."
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'subscribed'
        )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        self.user.first_name = first_name
        self.user.last_name = last_name
        profile = UserProfile.objects.create(user=self.user)
        if commit:
            self.user.save()
        return self.user


class EmailChangeForm(forms.Form):
    """
    A form that lets a user change set their email while checking for a change in the
    e-mail.
    """
    error_messages = {
        'email_mismatch': _("The two email addresses fields didn't match."),
        'not_changed': _("The email address is the same as the one already defined."),
    }

    new_email1 = forms.EmailField(
        label=_("New email address"),
        widget=forms.EmailInput(attrs={'placeholder': 'New email'}),
    )

    new_email2 = forms.EmailField(
        label=_("New email address confirmation"),
        widget=forms.EmailInput(attrs={'placeholder': 'Confirm new email'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EmailChangeForm, self).__init__(*args, **kwargs)

    def clean_new_email1(self):
        old_email = self.user.email
        new_email1 = self.cleaned_data.get('new_email1')
        if new_email1 and old_email:
            if new_email1 == old_email:
                raise forms.ValidationError(
                    self.error_messages['not_changed'],
                code='not_changed',
                )
        return new_email1

    def clean_new_email2(self):
        new_email1 = self.cleaned_data.get('new_email1')
        new_email2 = self.cleaned_data.get('new_email2')
        if new_email1 and new_email2:
            if new_email1 != new_email2:
                raise forms.ValidationError(
                    self.error_messages['email_mismatch'],
                    code='email_mismatch',
                )
        return new_email2

    def save(self, commit=True):
        email = self.cleaned_data["new_email1"]
        self.user.email = email
        if commit:
            self.user.save()
        return self.user