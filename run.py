import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting COP31 Backend on http://127.0.0.1:{port}")
    print(f"Swagger Documentation: http://127.0.0.1:{port}/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
