import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Load environment variables from .env if present
load_dotenv()

ACCESS_TOKEN = os.getenv("HYDI_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Hydi Voice Backend")

# Serve static frontend from /static and expose root index
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=os.path.abspath(static_dir)), name="static")


class RespondRequest(BaseModel):
    message: str
    sessionId: str | None = None


@app.get("/")
async def index():
    return FileResponse(os.path.abspath(os.path.join(static_dir, "index.html")))


@app.post("/api/respond")
async def respond(request: Request, body: RespondRequest):
    # Simple bearer token check if configured
    if ACCESS_TOKEN:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header.split(" ", 1)[1] != ACCESS_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")

    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # If OpenAI key available, use it for a better reply; otherwise fallback
    reply_text = await generate_reply(user_message)
    return JSONResponse({"reply": reply_text})


async def generate_reply(user_message: str) -> str:
    # Fallback behavior if no OpenAI key present
    if not OPENAI_API_KEY:
        return f"You said: {user_message}"

    try:
        # Lazy import to avoid dependency if unused
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Hydi, a concise, helpful assistant. Reply briefly."},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        reply = completion.choices[0].message.content or ""
        return reply.strip() or "(No response)"
    except Exception as e:
        # Graceful fallback
        return f"(Local reply) You said: {user_message}"


# Helpful startup log
@app.on_event("startup")
async def on_startup():
    print("Hydi Voice Backend starting...")
    if ACCESS_TOKEN:
        print("- Access token is configured; frontend must send Authorization: Bearer <token>.")
    else:
        print("- No access token set. Consider setting HYDI_ACCESS_TOKEN for privacy.")
    if OPENAI_API_KEY:
        print("- OpenAI is enabled for higher-quality replies.")
    else:
        print("- OpenAI not configured. Using local echo replies.")