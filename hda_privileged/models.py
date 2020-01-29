from time import gmtime, strftime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat
from django.db.models.signals import post_save

from django.dispatch import receiver

from django.utils.text import slugify


# helper functions
def get_sentinel_user():
    """
    Returns a special user object to represent a user that is no longer in the system

    """
    return get_user_model().objects.get_or_create(username='deleted user').first()

# Extend User Model Using a One-To-One Link


class Profile(models.Model):
    # Uses a onetoone User model extension field as a choice field, with 2 choices available
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    USER_TYPE = (('AD', 'Administrator'), ('AS', 'Assistant'),)
    utype = models.CharField(max_length=2, choices=USER_TYPE, default='AS')

    # post_save signal hooks create_user_profile and save_user_profile methods
    # to User model when save event occurs
    # signals ensure Profile model is automatically created/updated when we
    # create/update User instances
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


def get_upload_path(instance, filename):
    """

    :param instance: 
    :param filename: 

    """
    nowgmt = gmtime()
    datestr = strftime("%Y-%m-%d", nowgmt)
    timestr = strftime("%H-%M-%S", nowgmt)
    return "uploads/{0}/{1}-{2}".format(datestr, timestr, filename)


# model classes

class Health_Indicator(models.Model):
    """
    Represents some health metric that we want to store data sets for,
    e.g. obesity, mortality, education, etc.

    """
    name = models.CharField(max_length=100, unique=True)
    important = models.BooleanField(
        default=False,
        verbose_name='Show on overview',
        help_text='Display a chart for this indicator on the overview page for a state or county'
    )
    slug = models.SlugField()

    def save(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        if self.slug is None or self.slug == '':
            self.slug = slugify(self.name)
        super(Health_Indicator, self).save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} ({self.id})"

    class Meta:
        """ """
        verbose_name = 'Health indicator'


class Document(models.Model):
    """
    Represents a file that a privilged user uploads containing data to process
    """

    # where they got the data from
    source = models.CharField(
        max_length=144,
        blank=True,
        verbose_name="Data source",
        help_text="Describes where this data came from"

    )

    # when the file was uploaded (set automatically)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # user who uploaded the file (must be set in the view handling the upload)
    # is reset to a sentinel object if original user is deleted from the DB
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET(get_sentinel_user)
    )

    # the file
    file = models.FileField(upload_to=get_upload_path)


class Data_Set(models.Model):
    """
    A collection of data points for a single year and health indicator, generated from a document
    """

    # the health indicator/metric this data set is for
    indicator = models.ForeignKey(
        Health_Indicator,
        # do not allow indicator deletion if it is a foreign key in a dataset
        on_delete=models.PROTECT,
        related_name="data_sets"
    )
    # the year this data set covers
    # (not a date because we probably won't have an exact date)
    year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1000, message="Years before 1000 C.E. are extremely unlikely..."),
            MaxValueValidator(9999, message="If it really is later than the year 9999?"),
        ]
    )

    # the document this data set was generated from
    source_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_sets'
    )

    def __str__(self):
        return f"Dataset {self.id} for indicator {self.indicator!s} and year {self.year:d}"

    class Meta:
        """

        """
        verbose_name = 'Data set'


class US_State(models.Model):
    """
    Represents a state in the U.S. (e.g. Wyoming, Virginia)
    We populate the DB with a known-good set of these; they should not be user-generated

    """
    short = models.CharField(primary_key=True, max_length=2)
    full = models.CharField(max_length=100)
    # Char instead of int because, like a phone number, we don't want to truncate leading zeros!
    fips = models.CharField(max_length=2)

    def __str__(self):
        return self.fips + ' - ' + self.short + ' - ' + self.full

    class Meta:
        """
        """
        verbose_name = 'US state'


# This overrides the default manager to add a new computed field to counties when
# they are read from the database. We could make this more efficient by actually
# storing the full 5-digit fips code for every county, rather than the partial code.
# Solution from here: https://stackoverflow.com/a/42491803/5111071
# We could add an @property to the model class, but this way we can use the property
# to filter a queryset!
class US_County_Manager(models.Manager):
    """
    QuerySet manager for US_County class to add *non-database* fields.
    
    A @property in the model cannot be used because QuerySets (eg. return
    value from .all()) are directly tied to the database Fields -
    this does not include @property attributes.

    """

    def get_queryset(self):
        """
        Overrides the models.Manager method
        """
        qs = super(US_County_Manager, self).get_queryset()
        # add the "fips5" property - full 5-digit FIPs code
        qs = qs.annotate(fips5=Concat('state__fips', 'fips'))
        # add the "search_str" property - a human readable string including the state USPS code,
        # that uniquely identifies this county (or very nearly so)
        # used for creating search tokens and autocomplete values
        qs = qs.annotate(search_str=Concat('name', Value(' '), 'state__short'))
        return qs


class US_County(models.Model):
    """
    Represents a county or county-equivalent in a State in the U.S.
    We populate the DB with a known-good set of these; they should not be user-generated

    """
    # overriden model manager
    objects = US_County_Manager()

    # database fields
    fips = models.CharField(max_length=3)
    name = models.CharField(max_length=200)
    state = models.ForeignKey(US_State, related_name='counties', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.fips} - {self.name} - {self.state_id}'

    class Meta:
        """

        """
        verbose_name = 'US county'
        verbose_name_plural = 'US counties'


class Data_Point(models.Model):
    """
    A single measurement for a particular county and data set

    """
    value = models.FloatField(
        default=0,
        help_text="The measured value for this county for this data set"
    )

    rank = models.FloatField(
        default=0,
        help_text="The percentile for this value fits in, ranking it among the rest of the set",
        validators=[
            MinValueValidator(0, message="Percentiles cannot be less than 0")
        ]
    )

    county = models.ForeignKey(US_County, models.CASCADE, related_name='data_points')

    data_set = models.ForeignKey(Data_Set, models.CASCADE, related_name='data_points')

    class Meta:
        """

        """
        verbose_name = 'Data point'


# As an alternative to this, if we need more efficiency we can pack arrays of percentile values
# into a bytearray (using the struct module) and save that in a model.ByteField.
class Percentile(models.Model):
    """
    Stores *one* of the percentile values associated with a particular data set.
    What I'm calling a "percentile value" is the value such that some percent of
    the other values in the data set are <= that value, e.g.
    p = 0.86, v = 490 -> 86% of the values in the data set are <= 490

    """

    # the "name" of this percentile - e.g. for instance to represent the 86th percentile,
    # this value should be 0.86 while for the 25.1 percentile, it would be .251
    rank = models.FloatField()

    # the value in the data set that marks the boundary for the rank. For example,
    # if our rank is 0.86 and 86% of the values in the data set are <= 456, then this
    # value would be 456. It needs to be a float field because we are not constraining
    # the kind of numbers in a data set - they may be integers or floats
    value = models.FloatField()

    # pointer back to the data set we belong to. This establishes a one-to-many relationship from
    # Data_Set to Percentile, where was say "One Data_Set has many Percentiles". After calculating
    # the percentile values using the Data_Points in a Data_Set, we can save them in the database
    # by creating instances of this class that reference a specific Data_Set instance.
    # To read them back, use the property 'percentiles' on a Data_Set instance.
    data_set = models.ForeignKey(Data_Set, models.CASCADE, related_name='percentiles')
