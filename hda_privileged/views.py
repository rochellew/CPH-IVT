from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db import transaction
# Error message for user if trying to delete a foreign key
from django.db.models.deletion import ProtectedError
# wraps import for custom decorator
from functools import wraps
import json

from .forms import LoginForm, UploadNewDataForm, HealthIndicatorForm, NewUserForm, ProfileForm
from .models import Document, Data_Set, Data_Point, Percentile, Health_Indicator, Profile
from .percentile import get_percentiles_for_points, assign_percentiles_to_points
from .upload_reading import read_data_points_from_file


# ------------------------------------------------
# The user_log-in function will handle the log in
# functionality and redirect the loggedin user to
# desired page
# ------------------------------------------------
def user_login(request):
    """

    :param request: 

    """
    form = LoginForm()
    next = ""
    if request.GET:
        next = request.GET['next']
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    # The 'sample' routing will be changed to the desired landing page
                    # that will be displayed after authenticated user logs in
                    # If there is no next page to rout to, the routing will go to the
                    # Default landing page
                    if next == "":
                        return redirect(reverse('priv:dashboard1'))
                    else:
                        # If there is a next page, the routing will automatical go to the
                        # next page after a user is authenticated
                        return redirect(next)
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    args = {'form': form, 'next': next}
    return render(request, 'hda_privileged/login.html', args)


def logout_view(request):
    """

    :param request: 

    """
    logout(request)
    return redirect('priv:login')


# custom decorator to check if user is admin for user management module: Hawkins
# tutorial followed: https://gist.github.com/canokay/7c76e38b1c403f24768583e49d22871c
# IMPORTANT!!!!
# If using this decorator on a class, it must be used within the class with a method
# that overrides the dispatcher for that class. See user_management class for example.


"""param:view_func: a python function that Django uses as an object
   returns: the python function as decorator for admin or superuser: or redirects to dashboard: returns a wrapped response"""


def admin_or_super_functiondecorator(view_func):
    def wrap(request, *args, **kwargs):
        # Get user then get user's profile
        p = request.user.profile.utype
        if p == 'AD' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # User is not admin or superuser but is assistant, redirect to dashboard
        else:
            return redirect('priv:dashboard1')

    return wrap


# User Management dashboard lists all users with links to reset a password, deactivate
# an account, or create a new user: Hawkins
"""param:TemplateView: Django generic class-based view
   returns: context: all user objects for display in template table"""


class user_management(TemplateView):
    template_name = 'hda_privileged/usr_mgmt.html'
    model = User
    fields = ('username', 'first_name', 'last_name')

    # https://docs.djangoproject.com/en/2.2/topics/class-based-views/intro/
    @method_decorator(admin_or_super_functiondecorator)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        :param **kwargs:
        """
        # call super to get the base context
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context


# Allows a specified user to create new user accounts.
# https://simpleisbetterthancomplex.com/tutorial/2017/02/18/how-to-create-user-sign-up-view.html
# Developed by Kim Hawkins


"""param:request: request objects pass state through the system
   returns: save user and redirect to login if POST request, else return create user form"""


# controls transactions explicitly
# If successful, changes are committed to db
# If exception, changes are rolled back
@transaction.atomic
@admin_or_super_functiondecorator
def CreateNewPrivUser(request):
    # If the user has clicked 'create user', get user data from form
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        # if user entries in both forms are valid
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            user.is_active = True
            # extra steps to tie custom profile field to new user
            # varied from tutorial here because of integrity error with user_id
            for field in profile_form.changed_data:
                setattr(user.profile, field,
                        profile_form.cleaned_data.get(field))
            user.profile.save()
            return redirect('priv:dashboard1')
    # else the user has not clicked 'create user', return blank form
    else:
        users = User.objects.all().select_related('profile')
        current = request.user
        p = users.filter(username=current.username)
        form = NewUserForm()
        profile_form = ProfileForm()
    return render(request, 'hda_privileged/create_user.html', {'form': form, 'profile_form': profile_form})


# Allows administrator to deactivate an active user.
# Developed by Feyi


class DelPrivUser(TemplateView):
    """
    update the user's privileges
    :param UpdateView:
    :return:
    """
    # model = Profile
    template_name = 'hda_privileged/deactivate_user.html'

    # https://docs.djangoproject.com/en/2.2/topics/class-based-views/intro/
    @method_decorator(admin_or_super_functiondecorator)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, user):
        selected_user = User.objects.filter(id=user).first()
        return render(request, 'hda_privileged/deactivate_user.html', {'user': selected_user})

    def post(self, request, user):
        """

        :param request:
        :param user:
        :return:

        """
        selected_user = User.objects.filter(id=user).first()
        selected_user.is_active = False
        selected_user.save()
        messages.success(request, 'The user was successfully deactivated')
        return redirect('priv:user_mgmt')


"""
    param: Django's generic TemplateView
    returns: selected_user: user that was clicked on user management template and passed through url param
    render: password reset template, user object for selected user, and Django's SetPasswordForm
    redirect: password change successful, redirect to user management page
    """


class PasswordReset(TemplateView):
    template_name = 'hda_privileged/password_reset.html'

    # https://docs.djangoproject.com/en/2.2/topics/class-based-views/intro/
    @method_decorator(admin_or_super_functiondecorator)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    # get user selected on user management dashboard from user id in url params
    def get_selected_user(self):
        selected_id = self.kwargs.get('user', None)
        selected_user = User.objects.filter(user_id=selected_id).first()
        return selected_user

    # get the user object and pass to Django's set password form
    # SetPasswordForm was used because it does not involve email
    # and admin will not be required to enter old pw (user forgot their password)
    def get(self, request, user):
        selected_user = User.objects.filter(id=user).first()
        form = SetPasswordForm(selected_user)
        return render(request, 'hda_privileged/password_reset.html', {'usr': selected_user, 'form': form})

    # form is being submitted; validate form. If successful: save new password, success message for user,
    # redirect to user management dashboard. If not successful, give user an error message, render form again.
    def post(self, request, user):
        selected_user = User.objects.filter(id=user).first()
        form = SetPasswordForm(selected_user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'The password was successfully updated')
            return redirect('priv:user_mgmt')
        else:
            messages.error(request, 'Please correct the error below')
        return render(request, 'hda_privileged/password_reset.html', {'usr': selected_user, 'form': form})

    # to create a new health indicator


class HealthIndicatorCreate(CreateView):
    """
    creates new health indicator
    """
    template_name = 'hda_privileged/create_metric.html'
    model = Health_Indicator
    form_class = HealthIndicatorForm
    success_url = reverse_lazy('priv:dashboard1')


class HealthIndicatorUpdate(UpdateView):
    """
    updates an existing health indicator
    """
    model = Health_Indicator
    fields = ('name', 'important')
    template_name = 'hda_privileged/update_metric_form.html'
    pk_url_kwarg = 'post_pk'

    # Django requires this method when using the UpdateView param above
    def get_success_url(self):
        """
        :param self

        """
        return reverse_lazy('priv:dashboard1')


# Allows user to delete an indicator. Indicators are protected and cannot be deleted if tied to data records.
# Developed by Kim Hawkins
class HealthIndicatorDelete(DeleteView):
    """

    :param DeleteView: Generic Class-Based View Django Template

    """
    model = Health_Indicator
    fields = ('name',)
    template_name = 'hda_privileged/delete_metric.html'
    pk_url_kwarg = 'post_pk'

    def delete(self, request, *args, **kwargs):
        """

        :param request: 
        :param *args: 
        :param **kwargs: 
        :returns: Returns current template with protected indicator error message

        """
        self.object = self.get_object()
        try:
            self.object.delete()
            # user can confirm indicator was deleted by reviewing list on dashboard
            return HttpResponseRedirect(reverse_lazy('priv:dashboard1'))
        except ProtectedError:
            msg = messages.add_message(
                self.request, messages.ERROR, ' is tied to existing datasets and cannot be deleted.')
        # This code found at https://stackoverflow.com/questions/39560175/django-redirect-to-same-page-after-post-method-using-class-based-views
        return HttpResponseRedirect(self.request.path_info, msg)


# to delete an existing dataset
class DataSetDelete(DeleteView):
    """
    deletes existing dataset
    """
    model = Data_Set
    fields = ('source_document.file',)
    template_name = 'hda_privileged/delete_dataset.html'
    pk_url_kwarg = 'post_pk'
    success_url = reverse_lazy('priv:dashboard1')

    def delete(self, request, *args, **kwargs):
        """

        :param request: 
        :param *args: 
        :param **kwargs: 

        """
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.success_url)


class PrivDashboardView(TemplateView):
    """
    displays privileged user's dashboard
    """
    template_name = 'hda_privileged/privdashboard.html'

    def get_context_data(self, **kwargs):
        """

        :param **kwargs: 

        """
        # call super to get the base context
        context = super().get_context_data(**kwargs)

        # get indicators for left side of view
        indicators = Health_Indicator.objects.all()
        context['indicators'] = indicators

        # did the URL specify an indicator? Get indicator and save in context
        selected_id = self.kwargs.get('indicator', None)
        # now check if that ID is valid - is there an indicator with that ID?
        # use filter + first because get will throw an error if the object doesn't exist;
        # whereas this will have a value of None if it doesn't exist
        selected_indicator = indicators.filter(pk=selected_id).first()
        context['selected_indicator'] = selected_indicator

        if selected_indicator is not None:
            # if a valid indiactor was selected, only show datasets from that indicator
            context['indicator_message'] = f'Data sets for {selected_indicator.name}'
            context['datasets'] = selected_indicator.data_sets.all()
        else:
            # otherwise, show all the data sets
            context['indicator_message'] = 'Data sets for all indicators'
            context['datasets'] = Data_Set.objects.all()

        return context


class UploadNewDataView(View):
    """
    upload new dataset
    """
    form_class = UploadNewDataForm
    template_name = 'hda_privileged/upload_metric.html'
    file_field_name = 'file'

    def _get_uploaded_file(self, request):
        """

        :param request: 

        """
        return request.FILES[self.file_field_name]

    def _check_file_ext(self, request):
        """

        :param request: 

        """
        uploaded_file = self._get_uploaded_file(request)

        okay = uploaded_file is not None and \
               uploaded_file.name.lower().endswith(('.csv'))

        if not okay:
            messages.warning(request, "Error in file upload, file was not CSV")

        return okay

    def _handle_form_submission(self, request, form):
        """

        :param request: 
        :param form: 

        """
        myfile = self._get_uploaded_file(request)

        # create a Document class instance
        doc = Document(
            file=myfile,
            source=form.cleaned_data['source']
        )

        # add a user if we have one
        if request.user.is_authenticated:
            doc.user = get_user(request)

        # this saves the file in the directory specified
        # in the Document model FileField.upload_to attribute
        # and saves the rest of the model in the database
        doc.save()
        messages.success(request, "Document uploaded successfully")

        # Create and save a Data Set here! ##
        indicator = form.cleaned_data['indicator']
        year = form.cleaned_data['year']

        data_set = Data_Set(
            indicator=indicator,
            year=year,
            source_document=doc
        )

        data_set.save()

        format_choice = form.cleaned_data['column_format']
        doc.file.open(mode='rt')
        # read_data_points_from_file returns two values: successful_datapoints, and unsuccessful datapoints
        successful_data_points, invalid_counties_and_states = read_data_points_from_file(doc.file, format_choice,
                                                                                         data_set)
        doc.file.close()

        # calculate the percentile-values for this data set
        percentile_values = get_percentiles_for_points(successful_data_points)

        # assign a percentile to each data point
        assign_percentiles_to_points(successful_data_points, percentile_values)

        # transform our list of tuples List<(P, PV)> into a list of Percentile model objects
        percentile_models = [Percentile(rank=p, value=pv, data_set=data_set) for (p, pv) in percentile_values]

        # save all the data points and percentile values using bulk_create, for speed
        Data_Point.objects.bulk_create(successful_data_points)
        Percentile.objects.bulk_create(percentile_models)
        #

        # This is mostly for debugging, but it's a useful example of using the messages API
        messages.info(request, f"Indicator was {indicator!s}")

        return invalid_counties_and_states

    def get(self, request, *args, **kwargs):
        """

        :param request: 
        :param *args: 
        :param **kwargs: 

        """
        # unbound form
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """

        :param request: 
        :param *args: 
        :param **kwargs: 

        """
        # bind the form
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid() and self._check_file_ext(request):
            # Is there a Django-y way of adding more validation?
            invalid_counties_and_states = self._handle_form_submission(request, form)

        return render(request, self.template_name,
                      {'form': form, 'invalid_counties_and_states': invalid_counties_and_states})


class HealthIndicator(TemplateView):
    """
    template view for health indiicators
    """
    model = Health_Indicator
    template_name = 'hda_privileged/create_metric.html'
    context_object_name = 'all_indicators_created'
