import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import ExtractionScript as es

class VagueDescription:
    def __init__(self):
        self.df = es.extract_from_db(description=True)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.inc_title = True

    def _prepare_data(self):
        self.df['title_and_description'] = self.df['title'].str.cat(self.df['description'], sep=' ', na_rep='')

    def train_model(self):
        if self.inc_title:
            self.model_embed = self.model.encode(self.df['title_and_description'])
        else:
            self.model_embed = self.model.encode(self.df['description'])

    def predict_description(self, query, book_id_only=True):
        self.query_encode = self.model.encode(query)
        self.score_list = cosine_similarity(self.model_embed, [self.query_encode])

        #print('Training Completed')

        temp_lst = list()
        for idx, score in enumerate(self.score_list):
            if score > 0:
                temp_lst.append((idx, score))

        temp_lst = sorted(temp_lst, key=lambda x: x[1], reverse=True)
        self.top_indices = [item[0] for item in temp_lst[:10]]

        if book_id_only:
            return self.df.iloc[self.top_indices, 0].to_list()
        else:
            return self.df.iloc[self.top_indices]
        
if __name__ == "__main__":
    import time

    train_start = time.perf_counter()
    vague_search = VagueDescription()
    vague_search._prepare_data()

    no_train_start = time.perf_counter()
    vague_search.train_model()
    print(vague_search.predict_description("Socratic Dialogue by plato", book_id_only=False)['title'])
    end = time.perf_counter()
    print(f"Training completed in {no_train_start - train_start:.4f} seconds")
    print(f"Search completed in {end - no_train_start:.4f} seconds")