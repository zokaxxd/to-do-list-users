from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, field_validator
import sqlite3
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "zoka_To_do_List_backend_api"
ALGORITHM = "HS256"
ACESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


#-----------------Token functions

def create_token(data: dict):
    dados = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    dados.update({"exp": expire})
    token = jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"Id": user_id, "email": email}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")


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
    cursor = conn.cursor()
    return conn, cursor

#-----------------Routes

@app.get("/users")
def all_users(name: str = None, limit: int = 10, offset: int = 0):
    conn, cursor = get_db()

    query = "SELECT * FROM users"
    params = ()

    if name: 
        query += " WHERE name LIKE ?"
        params = (f"%{name}%",)   
    if name:
        cursor.execute("SELECT COUNT(*) FROM users WHERE name LIKE ?", (f"%{name}%",))
    else:
        cursor.execute("SELECT COUNT(*) FROM users")

    total = cursor.fetchone()[0]

    query += " LIMIT ? OFFSET ?"
    params += (limit, offset)

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()

    users = [
        {
            "id": u[0],
            "name": u[1],
            "age": u[2],
            "email": u[3]
        }
        for u in data
    ]
    return{
        "total": total,
        "limit": limit,
        "offset": offset,
        "users": users
    }


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


@app.get("/profile")
def profile(user: dict = Depends(verify_token)):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user["Id"],))
    data = cursor.fetchone()
    conn.close()

    return {
        "your name": data[1],
        "your age": data[2],
        "your email": data[3]
    }


