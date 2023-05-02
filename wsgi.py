"""Application entry point."""
from signals import init_app

app = init_app()

if __name__ == "__main__":
    # app.run(debug=True)# '0.0.0.0'
    app.run(port=8001)
