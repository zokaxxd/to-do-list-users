import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#-----------model from users
class User(BaseModel):
    name: str
    age: int
    email: EmailStr
    password: str

#---------------table 

def create_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        name TEXT,
        age INTEGER,
        email TEXT UNIQUE,
        password TEXT
        )
    """)
    conn.commit()
    conn.close()

create_table()

def get_db():
    conn = sqlite3.connect('users.db')
    return conn

#-----------------Routes

@app.get("/")
def home():
    return {"message": "Welcome to the To Do List API!"}

@app.post("/users")
def create_user(User: User):
    conn, cursor = get_db()

    cursor.execute("SELECT * FROM users WHERE email = ?", (User.email,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    cursor.execute("INSERT INTO users (name, age, email, password) VALUES (?, ?, ?, ?)",
                (User.name, User.age, User.email, User.password)
            )
    conn.commit()
    conn.close()

    return {"message": "User created successfully!"}