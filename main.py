
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Connexion à la base de données
def init_db():
    conn = sqlite3.connect("clients.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            whatsapp TEXT,
            projet TEXT,
            budget REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Page Publique pour les clients
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/commander")
def commander(nom: str = Form(...), whatsapp: str = Form(...), projet: str = Form(...), budget: float = Form(...)):
    conn = sqlite3.connect("clients.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clients (nom, whatsapp, projet, budget) VALUES (?, ?, ?, ?)", (nom, whatsapp, projet, budget))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/merci", status_code=303)

@app.get("/merci")
def merci(request: Request):
    return templates.TemplateResponse("merci.html", {"request": request})

# Dashboard Admin Privé
@app.get("/admin")
def admin_dashboard(request: Request):
    conn = sqlite3.connect("clients.db")
    conn.row_factory = sqlite3.Row # Cette ligne permet d'accéder aux données par leur nom
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    
    total_prospects = len(clients)
    chiffre_affaires = sum(c["budget"] for c in clients) if clients else 0
    
    conn.close()
    return templates.TemplateResponse("admin.html", {
        "request": request, 
        "clients": clients, 
        "total_prospects": total_prospects, 
        "chiffre_affaires": chiffre_affaires
    })
