from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load HTML templates
templates = Jinja2Templates(directory="templates")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = DistilBertForSequenceClassification.from_pretrained("sentiment_model")
tokenizer = DistilBertTokenizer.from_pretrained("sentiment_model")

model.to(device)
model.eval()


class Review(BaseModel):
    text: str


# Homepage route (serves your website)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Prediction API
@app.post("/predict")
def predict(review: Review):

    inputs = tokenizer(
        review.text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=1)

    negative_prob = probs[0][0].item()
    positive_prob = probs[0][1].item()

    label = "Positive" if positive_prob > negative_prob else "Negative"

    return {
        "label": label,
        "positive": positive_prob,
        "negative": negative_prob
    }