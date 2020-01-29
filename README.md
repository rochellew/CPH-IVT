# ETSU CPH Indicator Visualization Tool #

A web application that provides visualization and ranking of national public health indicators for counties in the United States.

## Development Environment ##

This is a Python project using pip for package management, virtualenv for dependency isolation, and the Django web application framework for implementation.

### Prerequisites ###

1. Python 3.7.x
2. pip, the Python package manager ([howto](pip))
3. virtualenv or virtualenvwrapper ([windows](vew-win), [general](vew))

- virtualenvwrapper is recommended for ease of use
- As a possible future improvement, changing package management to [pipenv](pipenv) would combine and eliminate direct use of pip and virtualenv, as well as allowing the specification of separate development and production dependencies (similar to NPM)

[pip]: https://pip.pypa.io/en/stable/installing/
[vew]: https://virtualenvwrapper.readthedocs.io/en/latest/install.html#installation
[vew-win]: https://virtualenvwrapper.readthedocs.io/en/latest/install.html#windows-command-prompt
[pipenv]: https://pipenv.readthedocs.io/en/latest/

### Project Set Up ###

These steps assume you are using virtualenvwrapper

1. Clone this repository to a directory:
    - `git clone git@bitbucket.org:ninjapirates/health-data-django.git MY_DIRECTORY`
    - The above command needs SSH configured for Bitbucket, but you can also clone using the HTTPS URL on the projeect Bitbucket page
2. Change to the project directory:
    - `cd MY_DIRECTORY`
2. Create a Python virtual environment for the project:
    - `mkvirtualenv ivt -a . -r .\requirements\development.txt`
        - `-a` tells virtualenv wrapper to associate the project code directory with the virtual environment. Not strictly necessary, just nice for quality of life.
        - `-r` tells virtualenvwrapper to immediately install dependencies from the supplied pip requirements file after setting up the virtual environment.
3. Activate the virtual environment:
    - `workon ivt`
    - This changes your shell to use the virtual environment's version of Python, instead of the globally installed one, and makes the packages installed in the environment available
4. Set up a development SQLite database for the app to use:
    - `python manage.py migrate`
    - This will create a file db.sqlite with the project's data model applied for the app to use
    - This SQLite file is only used on your local machine; SQLite is *not* used for the deployed app
5. Run the unit tests:
    - `python manage.py test`
6. Launch the app:
    - `python manage.py runserver`
    - This starts the Django development server with the app running
    - You should be able to see the homepage at `localhost:8000` in a web browser

### Creating an app admin account ###

Because we are using Django's provided authentication system (django.contrib.auth) for user accounts, you can create a superuser-level user account using Django's management tool: `python manage.py createsuperuser`

https://docs.djangoproject.com/en/2.1/ref/django-admin/#createsuperuser

Whatever credentials you provide can then be used to access both the Django admin portal and our application's privileged user pages on a locally-served instance of the webapp.

### Dependency Changes ###

If the `requirements\development.txt` or `requirements\base.txt` files are changed (indicating a new, removed, or updated dependency), you can simply re-run `pip install -r requirements\development.txt`, and pip will replace currently installed versions of packages with newere version from the requirements file. pip may not automatically remove packages that have been removed from the requirements file, but you can see what you have installed with `pip list`, and remove anything you no longer need with `pip uninstall`.

### Schema Changes ###

If a change to the data model requires a change in the database schema, new migration files will be added, and your local development database will need to be updated to match. Usually this is as simple as running `python manage.py migrate` again, since Django will detect and apply the new schema migrations for you. You can view a list of detected migrations with `python manage.py showmigrations`; usually all migrations should have an "X" next to them to show that they have been applied.

If migration fails, often the easiest solution is to delete your `db.sqlite` file, and rebuild it from scratch (again using `python manage.py migrate`).

Refer to the documentation on Django's `manage.py` for more details on using it for tests, migrations, and as a server.

* * * * * *

## Architecture Overview ##

todo - overview of development vs production environments and the code organization

## Settings and Configuration ##

todo - overview of `settings.py`

## other to-dos ##

- static asset management
- development dependencies (e.g. flake8)
- integration with VS Code
