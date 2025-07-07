from fastapi import FastAPI, UploadFile
from fastapi import File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from .file_utils import detect_file_type, parse_pdf, parse_excel, parse_csv, parse_docx, parse_image, upload_to_s3
from .nlp_utils import summarize_text, extract_policies
from .database import SessionLocal, init_db
from .models import File, ExtractedData, Comment, User
import json
from fastapi import Depends
from sqlalchemy.orm import Session
import shutil
from fastapi.responses import JSONResponse
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter
import os
import requests
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import HTTPException, status
from .auth import authenticate_user, create_access_token, get_password_hash, get_user
from jose import JWTError, jwt
from fastapi import Header

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Dependency to get current user from JWT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY', 'supersecret'), algorithms=['HS256'])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...), db: Session = Depends(get_db)):
    contents = await file.read()
    file_type = detect_file_type(file.filename)
    file_url = upload_to_s3(contents, file.filename)
    if file_type == 'pdf':
        text = parse_pdf(contents)
    elif file_type == 'excel':
        text = parse_excel(contents)
    elif file_type == 'csv':
        text = parse_csv(contents)
    elif file_type == 'docx':
        text = parse_docx(contents)
    elif file_type == 'image':
        text = parse_image(contents)
    else:
        return {"error": "Unsupported file type"}
    summary = summarize_text(text)
    policies = extract_policies(text)
    # Store in DB
    db_file = File(filename=file.filename, content_type=file.content_type)
    db_file.file_url = file_url
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    db_data = ExtractedData(file_id=db_file.id, raw_text=text, summary=summary, policies=json.dumps(policies))
    db.add(db_data)
    db.commit()
    return {
        "filename": file.filename,
        "file_url": file_url,
        "summary": summary,
        "policies": policies
    }

@app.get("/files")
def list_files(db: Session = Depends(get_db)):
    files = db.query(File).all()
    result = []
    for f in files:
        data = db.query(ExtractedData).filter(ExtractedData.file_id == f.id).first()
        result.append({
            "id": f.id,
            "filename": f.filename,
            "file_url": getattr(f, 'file_url', None),
            "content_type": f.content_type,
            "upload_time": f.upload_time,
            "summary": data.summary if data else None,
            "policies": json.loads(data.policies) if data and data.policies else []
        })
    return JSONResponse(content=result)

@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    files = db.query(File).all()
    data = db.query(ExtractedData).all()
    summary = {
        "total_files": len(files),
        "file_types": dict(Counter([f.content_type for f in files])),
        "total_policies": sum([len(json.loads(d.policies)) for d in data if d.policies]),
    }
    return summary

@app.get("/analytics/anomalies")
def analytics_anomalies(db: Session = Depends(get_db)):
    data = db.query(ExtractedData).all()
    lengths = [len(d.raw_text) for d in data if d.raw_text]
    if len(lengths) < 2:
        return {"anomalies": []}
    X = pd.DataFrame(lengths, columns=["length"])
    clf = IsolationForest(contamination=0.2)
    preds = clf.fit_predict(X)
    anomalies = [data[i].file_id for i, p in enumerate(preds) if p == -1]
    return {"anomalies": anomalies}

@app.get("/analytics/policies")
def analytics_policies(db: Session = Depends(get_db)):
    data = db.query(ExtractedData).all()
    all_policies = []
    for d in data:
        if d.policies:
            all_policies.extend(json.loads(d.policies))
    if not all_policies:
        return {"clusters": []}
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(all_policies)
    n_clusters = min(3, len(all_policies))
    if n_clusters < 2:
        return {"clusters": [[p] for p in all_policies]}
    kmeans = KMeans(n_clusters=n_clusters, n_init=10)
    labels = kmeans.fit_predict(X)
    clusters = [[] for _ in range(n_clusters)]
    for i, label in enumerate(labels):
        clusters[label].append(all_policies[i])
    return {"clusters": clusters}

@app.get("/enrich/topic")
def enrich_topic(q: str):
    # Use Bing Web Search API (or Google Custom Search if preferred)
    api_key = os.getenv('BING_API_KEY')
    if not api_key:
        return {"error": "Bing API key not set"}
    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": q, "count": 5}
    resp = requests.get(endpoint, headers=headers, params=params)
    if resp.status_code != 200:
        return {"error": "Web search failed"}
    data = resp.json()
    results = []
    for w in data.get("webPages", {}).get("value", []):
        results.append({"name": w["name"], "url": w["url"], "snippet": w["snippet"]})
    return {"results": results}

@app.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if get_user(db, form.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    user = User(username=form.username, hashed_password=get_password_hash(form.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered"}

@app.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected endpoint
@app.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@app.post("/comment")
def add_comment(file_id: int, content: str, policy_text: str = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = Comment(file_id=file_id, user_id=current_user.id, content=content, policy_text=policy_text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"msg": "Comment added"}

@app.get("/comments/{file_id}")
def get_comments(file_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.file_id == file_id).order_by(Comment.timestamp.desc()).all()
    return [
        {
            "user": c.user.username,
            "content": c.content,
            "policy_text": c.policy_text,
            "timestamp": c.timestamp
        }
        for c in comments
    ] 