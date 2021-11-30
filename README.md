# Installation

0. Clone and go into the cloned directory

```
git clone https://github.com/FSTUM/finanztool-v2.git
cd finanztool-v2
```

1. Install system dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv texlive-base texlive-lang-german texlive-fonts-recommended texlive-latex-extra
```

2. Install python-dependencies in an virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

# Development

1. Install additional dependencies after you installed the dependencies listed in [Installation](#installation)

```bash
sudo apt-get install -y gettext npm
python3 -m pip install -r requirements_dev.txt
```

2. Set the `DJANGO_SETTINGS_MODULE` environment option:

This Step is needed, because we have to have multiple settings files.
The `finanz.settings.keycloak_settings`-file uses keycloak, but because we DONT want to commit the secrets to git, this config is not useful for development (except if you want to test if keycloak works).  
The `finanz.settings.dev_settings`-file uses django's default [modelbackend](https://docs.djangoproject.com/en/3.2/ref/contrib/auth/) for authorisation.
This backend can be populated with a user using the [fixture](#sample-data-fixtures), or the `createsuperuser` command mentioned below.
The `finanz.settings.staging_settings`-file is only used in the staging environment.

```bash
export DJANGO_SETTINGS_MODULE=finanz.settings.dev_settings
```

3. Create the SQLite-database by running the following command inside the project directory:

```bash
python3 manage.py migrate
```

4. (Optional step, a user can be created using the [fixture](#sample-data-fixtures) below) Create an admin-account by running the following command inside the project directory:

```bash
python3 manage.py createsuperuser
```

Note that this doesn't set the `fist_name`, thus the `username` is shown on the website. If you want your `fist_name` to
be shown instead, you have to add your fist name in the admin interface.

5. Start the local webserver

```bash
python3 manage.py runserver
```

You can now visit http://localhost:8000/ in your browser

## pre-commit

Code quality is ensured via various tools bundled in [`pre-commit`](https://github.com/pre-commit/pre-commit/).

You can install `pre-commit`, so it will automatically run on every commit:

```bash
pre-commit install
```

This will check all files modified by your commit and will prevent the commit if a hook fails. To check all files, you
can run

```bash
pre-commit run --all-files
```

This will also be run by CI if you push to the repository.

## Sample-Data/ "Fixtures"

you can generate example-data (overrides every model with data that looks partially plausible, but is clearly not
production-data)
by opening the django shell using:

```shell
python3 manage.py shell
```

In the shell type

```python
import common.fixture as fixture
fixture.showroom_fixture_state()
```

This operation might take a few seconds. Don't worry.

## Adding Depenencies

If you want to add a dependency that is in `pip` add it to the appropriate `requirements`-file.  
If you want to add a dependency that is in `npm` run `npm i DEPENDENCY`. **Make shure that you do only commit the
nessesary files to git.**

# Staging

An staging environment is offered at [finanz.frank.elsinga.de](https://finanz.frank.elsinga.de).  
The username is `password`.  
The password is `username`.

## Building and running the dockerfile for local development

1. you need to save your environment variables in an `.env`-file.
   The further guide assumes content similar to the following in `staging/.env`.

```
DJANGO_DEBUG="True"
DJANGO_SECRET_KEY="CHOOSE_A_SAVE_PASSWORD"
DJANGO_ALLOWED_HOSTS="0.0.0.0,localhost,127.0.0.1"
```

2. Build the dockerfile

```
docker build -t finanztool-staging:v1 .
```

3. Run the Dockerfile

```
docker run --env-file staging/.env -p 8080:8000 finanztool-staging:v1
```

The Staging instance is now availibe at [`127.0.0.1:8080`](http://127.0.0.1:8080/) and is pushed to the Github Container Registry for convinience.
