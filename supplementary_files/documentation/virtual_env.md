# Using a Virtual Environment

This repository can be run locally or through a virtual environment. A virtual environment is recommended to avoid potential dependency and/or versioning issues. 

If you virtual environment has not been created yet, you can do so with:

```bash
virtualenv env 
```

To activate the virtual environment on Windows:

```bash 
env/Scripts/activate
```

To start the virtual environemnt on MacOS/Linus:

```bash
source env/bin/activate
```

Then install the project dependencies using:

```bash
(env) pip install -r requirements.txt
```