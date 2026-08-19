import os

import uvicorn

port = int(os.environ.get("PORT", "8000"))
uvicorn.run("commercial_app:app", host="0.0.0.0", port=port, reload=False)
