# MyStyle-AI

<img src="image.png" alt="MyStyle-AI Logo" width="160"/>


# 🛍️ Shopping AI Assistant

A full-stack, AI-powered shopping assistant built with real Myntra product data and synthetic behavioral insights. This project combines machine learning, deep learning, LLMs, and AI agents to simulate an intelligent e-commerce platform experience.

---

## 🚀 Features

### 🔍 Smart Product Search
- **Keyword and semantic search** using product title and descriptions
- **OpenAI embeddings** and **vector store (FAISS)** for similarity-based retrieval
- Query examples:
  - “Show me budget-friendly running shoes”
  - “T-shirts with high ratings under ₹500”

### 🤖 AI-Powered Chat Assistant
- LLM-based chatbot trained to:
  - Answer product-related queries
  - Handle simulated orders and returns
  - Act as a customer support agent (LangChain Agents)

### 🧠 Recommender System
- Collaborative filtering using simulated interaction logs
- Product-to-product recommendation based on user behavior
- Personalized suggestions for viewed/purchased products

### 📝 Review Sentiment Analysis
- Analyze synthetic or public dataset-based customer reviews
- NLP model (BERT/VADER) to classify review sentiment
- Insights into top-rated and low-rated items

### 🖼️ Product Image Classifier
- CNN model trained on product images
- Predict product category from visual input
- Supports training from scraped image dataset

### 📦 Order & Support Simulation
- Synthetic order logs with:
  - Order status (delivered, returned)
  - Support requests (refunds, complaints)
- Agent-based interaction flow for status updates or returns

---

## 📂 Project Structure

```
mystyle-ai/
├── data/
│   ├── products/
│   ├── images/
│   ├── reviews.csv
│   ├── orders.csv
│   └── user_interactions.csv
├── models/
├── notebooks/
├── scripts/
│   ├── scrape_myntra.py
│   ├── generate_interactions.py
│   └── simulate_orders_reviews.py
├── ui/
│   └── streamlit_app.py
└── README.md
```

---

## 🧠 Technologies Used

| Domain        | Tools |
|---------------|-------|
| Web Scraping  | Playwright (Async), Pandas |
| LLMs          | OpenAI GPT-4, LangChain |
| NLP           | BERT, VADER, SpaCy |
| ML / DL       | Scikit-learn, XGBoost, TensorFlow / PyTorch |
| UI            | Streamlit |
| Data Store    | FAISS, SQLite |
| Agent Flow    | LangChain Tools, Prompt Templates |

---

## 📊 Dataset Summary

| Dataset                | Source          |
|------------------------|-----------------|
| Product Catalog        | Scrapped (Myntra.com) |
| Review Data            | Public (Amazon/Yelp/Kaggle) |
| User Interactions      | Synthetic        |
| Order Logs             | Synthetic        |
| Product Images         | Scraped (Myntra.com)|

---

## 📦 Setup Instructions

```bash
git clone https://github.com/yourusername/smartshop-ai.git
cd smartshop-ai
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
```

---

## 🤝 Contributing

Contributions are welcome! Open an issue or submit a PR to improve functionality, UI, or model performance.

---

## 📜 License

MIT License. For educational purposes only. Data scraping adheres to fair use and ethical AI principles.