from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, field_validator
import sqlite3
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
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

#-------------password hash

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])
def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password[:72], hashed_password)


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
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired")


#-----------model from users
class User(BaseModel):
    name: str
    age: int
    email: EmailStr
    password: str

class TaskCreate(BaseModel):
    title: str
    

#---------------tables 
def create_table_tasks():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        completed INTEGER DEFAULT 0,
        user_id INTEGER
        )
        """)
    conn.commit()
    conn.close()
create_table_tasks()

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
    
    senha_hash = hash_password(User.password)
    
    cursor.execute("INSERT INTO users (email, password, age, name) VALUES (?, ?, ?, ?)",
                (User.email, senha_hash, User.age, User.name)
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

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn, cursor = get_db()

    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if not verify_password(form_data.password, user[4]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    token = create_token({"sub": str(user[0]), "email": user[3]})

    return {"access_token": token, "token_type": "bearer"}

@app.post("/tasks")
def create_task(task: TaskCreate, user: dict = Depends(verify_token)):
    conn, cursor = get_db()
    cursor.execute("INSERT INTO tasks (title, user_id) VALUES (?,  ?)",
                    (task.title, user["Id"])
                )
    conn.commit()
    conn.close()

    return {"message": "Task created successfully!"}

@app.get("/tasks")
def get_tasks(user: dict = Depends(verify_token)):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user["Id"],))
    data = cursor.fetchall()
    conn.close()

    tasks = [
        {
            "id": t[0],
            "title": t[1],
            "completed": bool(t[2])
        }
        for t in data
    ]
    return {"tasks": tasks}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, user: dict = Depends(verify_token)):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["Id"]))
    existing_task = cursor.fetchone()

    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?",
                (task_id, user["Id"]))
                
    conn.commit()
    conn.close()

    return {"message": "Task updated successfully!"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, user: dict = Depends(verify_token)):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["Id"]))
    existing_task = cursor.fetchone()

    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user["Id"]))
    conn.commit()
    conn.close()

    return {"message": "Task deleted successfully!"}