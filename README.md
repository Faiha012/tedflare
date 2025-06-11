# 🎤 TEDFLARE – TED Talks Recommendation System

TEDFLARE recommends TED Talks based on what users like or watch.  
It uses TF-IDF, cosine similarity, and Firebase to deliver personalized suggestions and securely manage user data.

---

## 🚀 Features

- 🔐 Firebase authentication (Signup/Login)  
- 💾 Save TED Talks  
- 👁️ Mark talks as watched  
- ❤️ Like/Unlike talks  
- 🤖 Get personalized recommendations  
- 🔍 Search TED Talks using natural language (e.g. "Talks about technology and AI")

---

## 🌐 Live App

Deployed using Streamlit Cloud  
👉 [Click here to open](https://tedflare-gzv9cjuj6smrlmjzmojhbc.streamlit.app/)

---

## 🧠 Technologies Used

- Python  
- Streamlit  
- Firebase (Authentication + Firestore)  
- Scikit-learn (TF-IDF, Cosine Similarity)  
- Pandas, NumPy

---

## 🧪 Run Locally

1. **Clone this repo**:

```bash
git clone https://github.com/your-username/tedflare.git
cd tedflare


2. Create .streamlit/secrets.toml and paste your Firebase credentials:

[firebase]
project_id = "your_project_id"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "your-email@your-project.iam.gserviceaccount.com"
client_id = "your_client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-cert-url"
universe_domain = "googleapis.com"


3. Install packages:

pip install -r requirements.txt


4. Run

streamlit run app.py



## 👩‍💻 Developed By

**Faiha Fathima M R**  
Developed as part of academic project work.


## 📃 License

This project is for educational use only.  
Do not upload your Firebase credentials to public repositories.


