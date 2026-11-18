# FlickFeel – AI Movie Review Sentiment Analyzer

## Overview

FlickFeel is an AI-powered movie review sentiment analysis application that classifies textual movie reviews into Positive and Negative sentiment categories using Natural Language Processing (NLP) and the DistilBERT transformer model.

The application provides an interactive interface where users can submit movie reviews, receive sentiment predictions, and view associated confidence scores.

## Problem Statement

Online movie platforms generate large volumes of user reviews. Manually analyzing these reviews to understand audience sentiment is time-consuming.

FlickFeel automates this process using transformer-based sentiment classification, enabling efficient identification of positive and negative opinions expressed in movie reviews.

## Key Features

- Binary sentiment classification (Positive / Negative).
- DistilBERT-based contextual text analysis.
- Sentiment probability and confidence scores.
- Interactive Streamlit interface.
- Sample reviews for testing predictions.
- Sentiment analysis history.
- Movie genre-based navigation.
- Dark and light interface themes.
- Rule-based fallback classification when the trained model is unavailable.

## Model Performance

| Evaluation Metric | Score |
|---|---:|
| Accuracy | 91.99% |
| F1 Score | 92.09% |
| AUC Score | 0.976 |
| Dataset Size | 50,000 IMDb Reviews |

*Note: These are the evaluation metrics reported within the application.*

## Methodology

The application follows the workflow below:

1. **Input:** The user submits a movie review.
2. **Tokenization:** The review is converted into tokens using the DistilBERT tokenizer.
3. **Model Inference:** The tokenized input is processed by the trained DistilBERT classification model.
4. **Probability Calculation:** Softmax converts the model outputs into class probabilities.
5. **Classification:** The sentiment category with the highest probability is selected.
6. **Output:** The application displays the predicted sentiment and confidence score.

If the trained model is unavailable, a rule-based keyword classifier is used as a fallback.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Deep Learning | PyTorch |
| NLP | Hugging Face Transformers |
| Pre-trained Model | DistilBERT |
| Web Framework | Streamlit |
| API Framework | FastAPI |
| Frontend | HTML, CSS, JavaScript |

## Project Structure

```text
FlickFeel/
│
├── app.py
├── api.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
├── report/
│
├── sentiment_model/
│
└── README.md
```

The `sentiment_model/` directory contains the locally saved trained model and tokenizer files. It must be available for DistilBERT-based inference.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/7ananya/FlickFeel---AI-Movie-Review-Sentiment-Analyzer-.git
```

### 2. Navigate to the Project Directory

```bash
cd FlickFeel---AI-Movie-Review-Sentiment-Analyzer-
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Streamlit Application

```bash
streamlit run app.py
```

The application will be accessible through the local browser.

## Running the FastAPI Backend

Install the additional dependencies:

```bash
pip install fastapi uvicorn jinja2 pydantic
```

Start the API server:

```bash
uvicorn api:app --reload
```

API endpoint:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

The FastAPI backend also requires the trained model directory and frontend template.

## Example

**Input:**

```text
The movie was absolutely brilliant.
The performances were outstanding
and the storyline kept me engaged.
```

**Expected Output:**

```text
Sentiment: POSITIVE
Confidence: Model-dependent
```

## Future Enhancements

- Multi-class sentiment classification.
- Aspect-based sentiment analysis.
- Movie-wise sentiment aggregation and visualization.
- Integration with external movie review platforms.
- Improved detection of sarcasm and contextual expressions.

## Author

**Ananya Terwadkar**

LIVE DEMO : https://flickfeel.streamlit.app/

[GitHub Profile](https://github.com/7ananya)

---

If you find this project useful, consider starring the repository.
