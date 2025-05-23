# FastAPI - Development

## Docker Compose

- Start the local stack with Docker Compose:

```bash
docker compose watch
```

- Now you can open your browser and interact with these URLs:

API, JSON based web API based on OpenAPI: http://localhost:8000

Automatic interactive documentation with Swagger UI (from the OpenAPI backend): http://localhost:8000/docs

Adminer, database web administration: http://localhost:8080

To check the logs, run (in another terminal):

```bash
docker compose logs
```

To check the logs of a specific service, add the name of the service, e.g.:

```bash
docker compose logs app
```

## Local Development

The Docker Compose files are configured so that each of the services is available in a different port in `localhost`.

You can run an idnividual service by running:

```bash
docker compose start service_name
```

Eg.

```bash
docker compose start app
```

You can stop that `app` service in the Docker Compose, in another terminal, run:

```bash
docker compose stop app
```

This applies for all other services:

## The .env file

The `.env` file is the one that contains all your configurations, generated keys and passwords, etc.

## Pre-commits and code linting

we are using a tool called [pre-commit](https://pre-commit.com/) for code linting and formatting.

When you install it, it runs right before making a commit in git. This way it ensures that the code is consistent and formatted even before it is committed.

You can find a file `.pre-commit-config.yaml` with configurations at the root of the project.

#### Install pre-commit to run automatically

`pre-commit` is already part of the dependencies of the project, but you could also install it globally if you prefer to, following [the official pre-commit docs](https://pre-commit.com/).

After having the `pre-commit` tool installed and available, you need to "install" it in the local repository, so that it runs automatically before each commit.

Using `uv`, you could do it with:

```bash
❯ uv run pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

Now whenever you try to commit, e.g. with:

```bash
git commit
```

...pre-commit will run and check and format the code you are about to commit, and will ask you to add that code (stage it) with git again before committing.

Then you can `git add` the modified/fixed files again and now you can commit.

#### Running pre-commit hooks manually

you can also run `pre-commit` manually on all the files, you can do it using `uv` with:

```bash
❯ uv run pre-commit run --all-files
check for added large files..............................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
ruff.....................................................................Passed
ruff-format..............................................................Passed
eslint...................................................................Passed
prettier.................................................................Passed
```

## URLs

The production or staging URLs would use these same paths, but with your own domain.

### Development URLs

Development URLs, for local development.

App: http://localhost:8000

Automatic Interactive Docs (Swagger UI): http://localhost:8000/docs

Automatic Alternative Docs (ReDoc): http://localhost:8000/redoc

Adminer: http://localhost:8080

## Commit message emoji guidlines

- ✨ **New Feature** – Add new functionality
- 🐛 **Bug Fix** – Fix a bug
- ♻️ **Refactor** – Code restructuring without behavior change
- 🔥 **Remove** – Delete code or files
- 📝 **Docs** – Documentation changes
- 🎨 **Style** – Code style changes (formatting, etc.)
- ✅ **Tests** – Add or update tests
- 🔧 **Config** – Update config/build scripts
- 🚀 **Performance** – Improve performance
- 💄 **UI** – Update UI styles
- 🚨 **Linter** – Fix compiler/linter warnings
- 🗃️ **DB** – Database related changes
- 🔒 **Security** – Fix security issues
- ⬆️ **Upgrade** – Upgrade dependencies
- ⬇️ **Downgrade** – Downgrade dependencies
- 👷 **CI** – CI/CD changes
- 📦 **Package** – Package-related changes
- 💥 **Breaking Change** – Breaking API/logic change
- ⏪ **Revert** – Revert previous commit
- 🚧 **WIP** – Work in progress
- 🧪 **Experiment** – Experimental code/tests

## Migrations

As during local development your app directory is mounted as a volume inside the container, you can also run the migrations with alembic commands inside the container and the migration code will be in your app directory (instead of being only inside the container). So you can add it to your git repository.

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

Start an interactive session in the app container:

```bash
docker compose exec app bash
```

Alembic is already configured to import your SQLModel models from ./backend/app/models.py.

After changing a model (for example, adding a column), inside the container, create a revision, e.g.:
```bash
alembic -c ./alembic.ini revision --autogenerate -m "Add column"
```

Commit to the git repository the files generated in the alembic directory.

After creating the revision, run the migration in the database (this is what will actually change the database):
```bash
alembic upgrade head
```
If you don't want to use migrations at all, uncomment the lines in the file at ./backend/app/core/db.py that end in:

SQLModel.metadata.create_all(engine)
and comment the line in the file scripts/prestart.sh that contains:

```bash
alembic upgrade head
```
If you don't want to start with the default models and want to remove them / modify them, from the beginning, without having any previous revision, you can remove the revision files (.py Python files) under ./backend/app/alembic/versions/. And then create a first migration as described above.
