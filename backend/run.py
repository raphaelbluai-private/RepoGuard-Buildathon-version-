import os

import uvicorn

# Docker/Railway entrypoint for the agent-commerce API. Railway normally injects
# PORT; default to the port used by the last known-good Railway deployment.
port = int(os.environ.get("PORT", "8080"))
uvicorn.run("commerce_app_v2:app", host="0.0.0.0", port=port, reload=False)
