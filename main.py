from fastapi import FastAPI, Form, Request, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader
import sqlite3
import re
import io
import csv

app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"))

conn = sqlite3.connect("clients.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        whatsapp TEXT,
        project_type TEXT,
        status TEXT,
        budget TEXT
    )
""")
conn.commit()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, search: str = Query(None), status_filter: str = Query(None)):
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR project_type LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status_filter and status_filter != "Tous":
        query += " AND status = ?"
        params.append(status_filter)

    cursor.execute(query, params)
    leads = cursor.fetchall()
    
    cursor.execute("SELECT * FROM leads")
    all_leads = cursor.fetchall()
    total_leads = len(all_leads)
    
    total_revenue = 0
    for lead in all_leads:
        budget_str = lead[5]
        numbers = re.findall(r'\d+', str(budget_str))
        if numbers:
            total_revenue += int(numbers[0])
            
    template = env.get_template("index.html")
    html_content = template.render(
        leads=leads, 
        total_leads=total_leads, 
        total_revenue=total_revenue,
        search=search or "",
        status_filter=status_filter or "Tous"
    )
    return HTMLResponse(content=html_content)

@app.post("/add")
async def add_lead(
    name: str = Form(...), 
    whatsapp: str = Form(...), 
    project_type: str = Form(...), 
    status: str = Form(...), 
    budget: str = Form(...)
):
    cursor.execute(
        "INSERT INTO leads (name, whatsapp, project_type, status, budget) VALUES (?, ?, ?, ?, ?)",
        (name, whatsapp, project_type, status, budget)
    )
    conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/update_status/{lead_id}")
async def update_status(lead_id: int = Path(...), status: str = Form(...)):
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete/{lead_id}")
async def delete_lead(lead_id: int = Path(...)):
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    return RedirectResponse(url="/", status_code=303)

# Nouvelle route pour exporter les clients en fichier CSV (lisible par Excel)
@app.get("/export")
async def export_csv():
    cursor.execute("SELECT name, whatsapp, project_type, status, budget FROM leads")
    leads = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    # En-têtes du fichier
    writer.writerow(["Nom du Client", "WhatsApp", "Type de Projet", "Statut", "Budget"])
    
    # Écriture des données
    for lead in leads:
        writer.writerow(lead)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mes_prospects_freelance.csv"}
    )