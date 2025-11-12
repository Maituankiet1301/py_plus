# py_plus / Flask Inventory skeleton

## Quick start


python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

 = "run.py"
flask db init
flask db migrate -m "init"
flask db upgrade

flask run
