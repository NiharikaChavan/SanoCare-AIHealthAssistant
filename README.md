# SanoCare AI Health Assistant

An AI-powered health assistant that provides personalized medical information and support using advanced language models and vector databases.

## Project Overview

SanoCare AI Health Assistant is a comprehensive healthcare platform that leverages artificial intelligence to provide personalized medical information and support. The system uses OpenAI's language models and Pinecone's vector database to deliver accurate and contextually relevant health information.

## Project Structure
```
SanoCare-AIHealthAssistant/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── src/               # Source code
├── templates/         # HTML templates
├── static/           # Static files (CSS, JS, images)
├── frontend/         # Frontend application
├── Data/             # Data storage and processing
├── research/         # Research and documentation
└── tests/            # Test files
```

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- PostgreSQL 12 or higher
- OpenAI API key
- Pinecone API key

## Backend Setup

1. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory with:
   ```
   SECRET_KEY=your_secret_key
   FLASK_ENV=development
   FLASK_APP=app.py
   SQLALCHEMY_DATABASE_URI=postgresql://postgres:root@localhost:5432/medicaldb
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   ```

4. **Initialize the database**
   ```bash
   python check_db.py
   ```

5. **Run the backend server**
   ```bash
   python app.py
   ```
   The backend will run on http://localhost:5000

## Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   Create a `.env` file in the frontend directory with:
   ```
   VITE_API_URL=http://localhost:5000
   VITE_ENV=development
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```
   The frontend will run on http://localhost:5173

## Key Features

- **User Authentication**
  - Secure registration and login system
  - Password hashing and session management
  - User profile management

- **AI-Powered Health Assistant**
  - Natural language processing for health queries
  - Personalized medical information
  - Context-aware responses
  - Integration with OpenAI's GPT models

- **Vector Database Integration**
  - Efficient medical information storage and retrieval
  - Semantic search capabilities
  - Real-time information updates

- **Database Management**
  - PostgreSQL for robust data storage
  - SQLAlchemy ORM for database operations
  - Automated database migrations

- **Responsive Frontend**
  - Modern React-based interface
  - Real-time updates
  - Mobile-friendly design
  - Interactive health assessment tools

## Technologies Used

### Backend
- Flask 3.0.2
- SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Flask-CORS 4.0.0
- PostgreSQL with psycopg2-binary 2.9.9
- OpenAI API 1.12.0
- Pinecone Client 3.0.2
- LangChain 0.1.12
- Sentence Transformers 2.5.1

### Frontend
- React
- Vite
- Modern JavaScript
- CSS/SCSS
- Axios for API calls

## Development

- Backend API runs on port 5000
- Frontend development server runs on port 5173
- Make sure both servers are running for full functionality
- Use `test_registration.py` and `test_db.py` for testing

## Testing

Run the test suite:
```bash
python test_registration.py
python test_db.py
```


## License

This project is licensed under the MIT License - see the LICENSE file for details

## Support

For support, please open an issue in the GitHub repository or contact the development team.
