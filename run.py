# run.py
from waitress import serve
from app import create_app

app = create_app()
mode = "prod"

if __name__ == '__main__':
    if mode == "prod":
        serve(app, host='0.0.0.0', port=4455)
    else:
        app.run(host='0.0.0.0', port=4455, debug=True)
    # serve(app, host='0.0.0.0', port=3000)