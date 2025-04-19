import random

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import RegexValidator, MinLengthValidator
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.utils.translation import gettext_lazy as _

from main.core.models import TimeStampedModel
from main.users.manager import UserManager

username_validator = ASCIIUsernameValidator()
_PHONE_REGEX = RegexValidator(regex=r'(\d{9,15})$',
                              message=_("Your phone number should consist of 9-15 digits. Example: 1114442277"))


def get_random_pin():
    return random.choice(range(100000, 999999))


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    email = models.EmailField(_('Email address'), default="", unique=True, blank=True)
    pin = models.PositiveIntegerField(_("PIN"), default=get_random_pin, validators=[MinLengthValidator(6)], )
    first_name = models.CharField(_('First name'), max_length=30, default="", blank=True)
    last_name = models.CharField(_('Last name'), max_length=30, default="", blank=True)
    birthdate = models.DateField(verbose_name=_("Birth Date"), null=True)
    is_staff = models.BooleanField(_('Is Staff'), default=False)
    is_active = models.BooleanField(_('Is Active'), default=False)
    is_verified = models.BooleanField(_('Is Verified'), default=False)
    is_email = models.BooleanField(_('Is Email Verified'), default=False)
    img = models.ImageField(verbose_name=_("Avatar"), upload_to=settings.DEFAULT_USER_FOLDER, blank=True,
                            default=settings.DEFAULT_USER_AVATAR)

    address = models.TextField(verbose_name=_("Address"), blank=True, )
    mob = models.CharField(verbose_name=_("Mobile"), max_length=15, blank=True, validators=[_PHONE_REGEX])
    tel = models.CharField(verbose_name=_("Telephone"), max_length=15, blank=True, validators=[_PHONE_REGEX])
    fax = models.CharField(verbose_name=_("Fax"), max_length=15, blank=True, validators=[_PHONE_REGEX])

    login_count = models.PositiveIntegerField(verbose_name=_("Login Count"), default=0)

    username_validator = ASCIIUsernameValidator()
    username = models.CharField(_('Username'), max_length=150, unique=True,
                                help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={
                                    'unique': _("A user with that username already exists."),
                                },
                                )

    objects = UserManager()
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    @property
    def date_joined(self):
        return self.created

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name) if self.first_name and self.last_name else self.username
        return full_name.strip()

    get_full_name.short_description = _("Full Name")

    def get_full_name_slug(self):
        return "{}-{}".format(self.get_full_name().replace(' ', '-'), self.pin)

    @property
    def fullname(self):
        return self.get_full_name()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name if self.first_name else self.username

    get_short_name.short_description = _("Short Name")

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name()

    def get_dict(self):
        return {
            "pk": self.pk,
            "img": {
                "url": self.img.url, "name": self.img.name
            } if isinstance(self.img, ImageFieldFile) else {
                "url": settings.DEFAULT_USER_AVATAR, "name": "user"
            },
            "username": self.username,
            "firstname": self.first_name,
            "lastname": self.last_name,
            "fullname": self.get_full_name(),
            "email": self.email,
            "created": self.created.isoformat() if self.created else None,
        }
