import codecs
import csv
import os

import apsw
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

conn = None

def init():
    fp = os.path.join(os.getcwd(), "data", "busse_lots.db")
    conn = apsw.Connection(fp)
    conn.execute("create table if not exists lots(lot text primary key, part text, expiration varchar(10)), on_hand int, allocated int")

    return conn

def get_all_lots():
    global conn

    lots = []

    cursor = conn.cursor()
    cursor.execute("select * from lots")
    for row in cursor:
        lots.append(row)

    return lots

def get_lot(lot):
    global conn

    cursor = conn.cursor()
    cursor.execute("select * from lots where lot=?", (lot,))

    for row in cursor:
        print(row)

    return row

def get_lots_by_part(part):
    global conn

    cursor = conn.cursor()
    cursor.execute("select * from lots where part=?", (part,))

    lots = []

    for row in cursor:
        lots.append(row)
    
    return lots

def delete_lot(lot):
    global conn

    conn.execute("delete from lots where lot=?", (lot,))

def count_lots():
    global conn

    cursor = conn.cursor()
    cursor.execute("select count(*) from lots")
    for row in cursor:
        print(row)

    return row[0]

@app.on_event("startup")
def startup_event():
    global conn
    conn = init()

@app.get("/update")
async def main():
    content = """
<body>
    <h1>Update `Lot` Database</h1>
    <strong>UPDATE.LOTS</strong> and the output is found at "C:/temp/LOTS.CSV"
    <form action="/update/" enctype="multipart/form-data" method="post">
        <input name="file" type="file">
        <input type="submit">
    </form>
</body>
    """
    return HTMLResponse(content=content)

@app.post("/update")
async def update(file: UploadFile = File(...)):
    global conn

    updates = []
    constraint_errors = 0
    
    reader = csv.reader(codecs.iterdecode(file.file, 'utf-8'))        

    for line in reader:            
        if len(line) > 1:
            lot = line[0].split("|")[0]
            part = line[1]            
            expiration = None
            oh_qty = line[3]
            alloc_qty = line[4]
            
            if "-" in line[2]:
                _expiration = line[2]
                month, date, _year = _expiration.split("-")
                year = "20" + _year
                expiration = f"{year}-{month}-{date}"
            
            if expiration:
                try:            
                    conn.execute("insert into lots(lot, part, expiration) values (?, ?, ?, ?, ?)", (lot, part, expiration, oh_qty, alloc_qty))

                    updates.append({
                        "lot": lot,
                        "part": part,
                        "expiration": expiration,
                        "on-hand": oh_qty,
                        "allocated": alloc_qty,
                    })

                except apsw.ConstraintError:
                    constraint_errors += 1

    counted_lots = count_lots()

    return { "updates": updates, "constraint_errors_count": constraint_errors, "count": counted_lots }

@app.get("/delete")
async def delete_form():
    content = """
<body>
    <h1>Delete `Lot`</h1>
    <form action="/delete/" method="post">
        <input name="lot" type="number">
        <input type="submit">
    </form>
</body>
    """
    return HTMLResponse(content=content)

@app.post("/delete")
async def delete(lot: str = Form(...)):
    global conn

    try:
        delete_lot(lot)
    except apsw.ConstraintError:
        return { "error": "lot not found" }

    return { "deleted": lot }

@app.get("/count")
async def count():
    return { "count": count_lots() }

@app.get("/")
async def get_by_lot(lot: str):
    try:
        lot_info = get_lot(lot)
    except apsw.ConstraintError:
        return { "error": "lot not found" }

    return { "lot": lot_info[0], "item": lot_info[1], "expiration": lot_info[2] }

@app.get("/all")
async def get_all_lots_api():
    try:
        lots = get_all_lots()
    except apsw.ConstraintError:
        return { "error": "lots not found" }

    return lots

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8089, reload=True)    
