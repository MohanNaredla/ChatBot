import os
import re 
import pickle 

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_community.embeddings import SentenceTransformerEmbeddings
from rank_bm25 import BM25Okapi

class Embedding:
    def __init__(self):
        self.role = 'District Absence Coordinator'
        self.data_path = f'data/manuals/{self.role} Manual.txt'

        
    def read_data(self) -> list:
         try:
             with open(self.data_path, 'r', encoding='utf-8') as file:
                 content = file.read()
                 content = re.sub('\u202f', ' ', content)
                 all_lines = [line for line in content.split('\n') if line.strip()]
                 return all_lines
             
         except Exception as e:
             print(f'File Not Found: {e}')
             return []
         
         
    def find_sections(self, all_lines) -> list:
        sec_regex = re.compile(r'^\d+\.\s+[A-Z]')
        section_indices = [i for i, line in enumerate(all_lines) if sec_regex.match(line)]
        
        if section_indices:
            section_indices.append(len(all_lines))
            
        return section_indices
    
    
    def extract_section_metadata(self, section_header) -> tuple[str, str]:
        section_parts = section_header.split(' ', 1)
        
        if len(section_parts) < 2:
            section_number = section_parts[0].rstrip('.')
            return section_number, ""
        
        section_number = section_parts[0].rstrip('.')
        section_title = section_parts[1].strip()
        
        return section_number, section_title
    
    
    def process_chunks(self):
        all_lines = self.read_data()
        if not all_lines:
            print("No data found in the manuals")
            return []
        
        section_indices = self.find_sections(all_lines)
        if not section_indices:
            print("No sections found in the manuals")
            return []
        
        subsec_pattern = re.compile(r'^\s*\d+\.\d+\s+[A-Z]')
        chunks = []
        
        for i in range(len(section_indices)-1):
            sec_start, sec_end = section_indices[i], section_indices[i+1]
            section_content = all_lines[sec_start:sec_end]
            
            section_header = section_content[0]
            section_number, section_title = self.extract_section_metadata(section_header=section_header)
            
            subsection_indices = [j for j, line in enumerate(section_content)
                                  if j > 0 and subsec_pattern.match(line)]
            
            if subsection_indices:
                subsection_indices.append(len(section_content))
                
                for k in range(len(subsection_indices)-1):
                    subsec_start, subsec_end = subsection_indices[k], subsection_indices[k+1]
                    subsec_content = section_content[subsec_start:subsec_end]
                    
                    subsec_header = subsec_content[0].strip()
                    subsec_parts = subsec_header.split(' ', 1)
                    
                    subsec_number, subsec_title = subsec_parts[0], subsec_parts[1].strip()
                    text_content = '\n'.join(subsec_content)
                    
                    metadata = {
                        'section': section_number,
                        'section_title': section_title,
                        'sub_section': subsec_number,
                        'sub_title': subsec_title
                    }
                    
                    chunks.append({
                        'metadata': metadata, 
                        'content': text_content
                        })
                
            else:
                text_content = "\n".join(section_content)
  
                metadata = {
                    "section": section_number,
                    "section_title": section_title,
                    "sub_section": "",
                    "sub_title": ""
                }
            
                chunks.append({
                    "metadata": metadata, 
                    "content": text_content
                    })
                
        return chunks
    
    
    def build_vector_database(self):
        chunks = self.process_chunks()
        docs = []
        
        for chunk in chunks:
            doc = Document(
                page_content=chunk['content'],
                metadata=chunk['metadata']
            )
            docs.append(doc)
            
        os.makedirs('data/index', exist_ok=True)
        embeddings = SentenceTransformerEmbeddings(
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        )
        vs = FAISS.from_documents(docs, embeddings)
        vs.save_local('data/index/faiss')
        
        texts = [doc.page_content for doc in docs]
        tokenized_texts = [text.split() for text in texts]
        bm_25 = BM25Okapi(tokenized_texts)
        meta = [doc.metadata for doc in docs]
    
        with open("data/index/bm25.pkl", "wb") as f:
            pickle.dump((bm_25, texts, meta), f)
    
    
obj = Embedding()
obj.build_vector_database()

with open("data/index/chunks_with_metadata.txt", "w", encoding="utf-8") as f:
    for chunk in obj.process_chunks():
        f.write(f"{chunk['metadata']}\n{chunk['content']}\n{'='*113}\n")