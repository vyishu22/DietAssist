from app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True') == 'True'
    # Disable the auto-reloader on Windows to avoid "not a socket" errors
    # caused by the reloader's thread interaction with selectors.
    app.run(debug=debug, port=port, host='0.0.0.0', use_reloader=False)
