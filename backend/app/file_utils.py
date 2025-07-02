import os
import io
from typing import Tuple, Any
from PIL import Image
import pytesseract
import pdfplumber
import pandas as pd
import docx
import boto3

S3_BUCKET = os.getenv('S3_BUCKET')
S3_KEY = os.getenv('S3_KEY')
S3_SECRET = os.getenv('S3_SECRET')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')

def detect_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.pdf']:
        return 'pdf'
    elif ext in ['.xls', '.xlsx']:
        return 'excel'
    elif ext in ['.csv']:
        return 'csv'
    elif ext in ['.docx']:
        return 'docx'
    elif ext in ['.jpg', '.jpeg', '.png']:
        return 'image'
    else:
        return 'unknown'

def parse_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() or ''
        return text

def parse_excel(file_bytes: bytes) -> str:
    df = pd.read_excel(io.BytesIO(file_bytes))
    return df.to_csv(index=False)

def parse_csv(file_bytes: bytes) -> str:
    df = pd.read_csv(io.BytesIO(file_bytes))
    return df.to_csv(index=False)

def parse_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return '\n'.join([p.text for p in doc.paragraphs])

def parse_image(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image)
    return text

def upload_to_s3(file_bytes: bytes, filename: str) -> str:
    if not S3_BUCKET or not S3_KEY or not S3_SECRET:
        # Fallback: save locally
        with open(f'uploads/{filename}', 'wb') as f:
            f.write(file_bytes)
        return f'local://uploads/{filename}'
    s3 = boto3.client('s3', aws_access_key_id=S3_KEY, aws_secret_access_key=S3_SECRET, region_name=S3_REGION)
    s3.put_object(Bucket=S3_BUCKET, Key=filename, Body=file_bytes)
    return f's3://{S3_BUCKET}/{filename}' 