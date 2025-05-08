class Data:
    def __init__(self):
        self.role = 'District Absence Coordinator'
        self.data_path = f'data/manuals/{self.role} Manual.txt'
        self.faiss_dir = f'data/index{self.role.split(' ')[0]}/faiss'
        self.bm25_dir = f'data/index{self.role.split(' ')[0]}/bm25.pkl'