import os
import string
import re
import difflib
import sys
from collections import defaultdict
import json
from datetime import time

from pydantic import BaseModel
import uvicorn
import pickle
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch

import openai
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retrieve:
    def __init__(self, query):
        self.top_k = 5
        self.vs_path = 'data/index/faiss'
        self.bm_path = 'data/index/bm25.pkl'
        self.query = query
        
    
        