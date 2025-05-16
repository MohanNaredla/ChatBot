# RAG Service
This is a simple web application that allows users to interact with a RAG server. It provides a user-friendly interface for sending messages and receiving responses from the RAG server.
## Overview
The `rag_service` module is a backend AI service. It serves as a user interface for interacting with openAI `ChatGPT 3.5 turbo`. The application allows users to send messages to a RAG server and receive responses in real-time instead of the request of query going to the RAG service.
## Features
- User-friendly interface for sending messages to RAG
- Real-time response display
- Integration with RAG server for natural language processing
- Support for multiple conversation sessions

## Installation
1. Navigate to the `rag_service` directory:
   ```bash
    cd rag_service
    ```
2. Create a virtual environment (optional but recommended):
    ```bash
    py -3.13 -m  venv venv
    source venv/bin/activate # For macOS/Linux
    venv\Scripts\activate # For Windows
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the RAG application:
    ```bash
    python index_documents.py
    python service.py
    ```
now as rag service is running you can setup the rasa_app. follow the instructions in of rasa_app readme.
