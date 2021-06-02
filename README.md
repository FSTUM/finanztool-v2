# Installation

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

2. Create the SQLite-database by running the following command inside the project directory:

```bash
python3 manage.py migrate
```

3. Create an admin-account by running the following command inside the project directory:

```bash
python3 manage.py createsuperuser
```

Note that this doesn't set the `fist_name`, thus the `username` is shown on the website. If you want your `fist_name` to
be shown instead, you have to add your fist name in the admin interface.

4. Start the local webserver

```bash
python3 manage.py runserver
```

    You can now visist http://localhost:8000/ in your browser

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
