from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()
DATABASE_NAME = os.environ.get("DATABASE_NAME", "jobs.db")
templates = Jinja2Templates(directory="templates")

def get_jobs():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, title, company_name, apply_url, location_city, location_state, location_country, remote, hybrid, last_seen, site_id, id FROM jobs GROUP BY job_id ORDER BY last_seen DESC, company_name, title")
    jobs = cursor.fetchall()
    conn.close()
    return jobs

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    jobs = get_jobs()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
