import os
import sys
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Sistem zorla baslatiliyor...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=9999, reload=True)
