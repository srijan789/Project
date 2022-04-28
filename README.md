# Steps to be followed: 
1) Create a virtual env with ``python -m venv .{{Foldername}}``
2) install all dependencies in the shell with  ``pip install -r requirements.txt``
3) Create data base by first running the python interpreter, then run ``>>> from main import db`` then 
``>>> db.create_all()``
4) Exit the interpreter
5) To run the flask app, on the shell, run ``python main.py``

Read the API Doc for API specifications