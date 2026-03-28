import sys
from streamlit.web import cli as stcli

def main():
    # Configure Streamlit to run in a way suitable for Electron embedding
    # We set server port and headless mode
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port", "8501",
        "--server.headless", "true",
        "--global.developmentMode", "false",
        "--browser.gatherUsageStats", "false"
    ]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
