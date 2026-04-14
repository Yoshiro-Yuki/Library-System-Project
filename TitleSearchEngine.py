from tracemalloc import start

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from nltk import PorterStemmer

import ExtractionScript as es

class SemanticTitleSearch:
    """A search engine that combines TF-IDF and BM25 for semantic book title matching.

    This class provides functionality to preprocess book data, train vectorization 
    models, and perform ensemble searches using weighted similarity scores.

    Attributes:
        df (pd.DataFrame): The dataframe containing raw and processed book data.
        tv_column (str): Column name for standard text vectorization.
        bm25_column (str): Column name for tokenized text used in BM25.
        tv_stemmed_column (str): Column name for stemmed text vectorization.
        weight_one (float): Weight for the standard TF-IDF cosine similarity score.
        weight_two (float): Weight for the BM25 relevance score.
        weight_three (float): Weight for the stemmed TF-IDF cosine similarity score.
    """

    def __init__(self):
        """Initializes the search engine with data and default scoring weights."""
        self.df = es.extract_from_db()
        self.tv_column = 'book_string_info'
        self.bm25_column = 'book_string_info_tokenized'
        self.tv_stemmed_column = 'book_string_info_stemmed'
        self.weight_one = 0.5
        self.weight_two = 0.35
        self.weight_three = 0.15

    def _word_stemmer(self, string):
        """Reduces words to their root form using the Porter Stemmer.

        Args:
            string (str): The raw text string to be stemmed.

        Returns:
            str: A string of space-separated stemmed tokens.
        """
        ps = PorterStemmer()
        string_token = string.split()
        return " ".join(ps.stem(word) for word in string_token)

    def _prep_data(self):
        """Preprocesses the dataframe by concatenating, cleaning, and stemming text."""
        self.df['book_string_info'] = self.df['title'].str.cat(self.df['category_name'], sep=' ', na_rep='')
        self.df['book_string_info'] = self.df['book_string_info'].str.lower()
        self.df['book_string_info_stemmed'] = self.df['book_string_info'].apply(self._word_stemmer)
        self.df['book_string_info_tokenized'] = self.df['book_string_info'].str.split()
            
    def train_engine(self):
        """Initializes and fits the TF-IDF and BM25 models on the preprocessed data."""
        self.tv_model = TfidfVectorizer()
        self.tv_stemmed_model = TfidfVectorizer()

        self._prep_data()

        self.tv_bag_words = self.tv_model.fit_transform(self.df[self.tv_column])
        self.tv_stemmed_bag_words = self.tv_stemmed_model.fit_transform(self.df[self.tv_stemmed_column])
        self.bm25 = BM25Okapi(self.df[self.bm25_column].tolist())

    def _prep_model_agents(self, bag_of_words=None, tvectorizer=None, vectorize_data=True):
        """Calculates similarity or relevance scores for the current prediction query.

        Args:
            bag_of_words (sparse matrix, optional): Precomputed TF-IDF matrix. Defaults to None.
            tvectorizer (TfidfVectorizer, optional): Fitted vectorizer instance. Defaults to None.
            vectorize_data (bool): If True, uses Cosine Similarity; if False, uses BM25.

        Returns:
            np.ndarray: A flattened array of scores corresponding to each row in the dataframe.
        """
        if vectorize_data:
            coss_agent = cosine_similarity(
                bag_of_words,
                tvectorizer.transform([self.predict])
            )
            return coss_agent.flatten()
        else:
            return self.bm25.get_scores(self.predict.split(" "))

    def _suggest_title(self):    
        """Calculates the final ensemble weighted similarity score across all models."""
        self.similarity_score_one_weighted = self._prep_model_agents(self.tv_bag_words, self.tv_model) * self.weight_one
        self.similarity_score_two_weighted = self._prep_model_agents(vectorize_data=False) * self.weight_two
        self.similarity_score_three_weighted = self._prep_model_agents(self.tv_stemmed_bag_words, self.tv_stemmed_model) * self.weight_three
        
        self.similarity_score_models = self.similarity_score_one_weighted + self.similarity_score_two_weighted + self.similarity_score_three_weighted

    def get_ten_titles_indices(self, predict, book_id_only=True):
        """Processes a search query and returns the top 10 most relevant books.

        Args:
            predict (str): The search query or book title to find matches for.

        Returns:
            pd.DataFrame: A slice of the original dataframe containing the top 10 results.
        """
        self.predict = predict
        self._suggest_title()
        self.combined_list = list()
        
        for ind, score in enumerate(self.similarity_score_models):
           if score > 0:
                self.combined_list.append((ind, float(score)))
        
        self.combined_list = sorted(self.combined_list, key=lambda x: x[1], reverse=True)
        self.combined_top_indices = [item[0] for item in self.combined_list[:10]]

        if book_id_only:
            return self.df.iloc[self.combined_top_indices, 0].to_list()
        else:
            return self.df.iloc[self.combined_top_indices]
        
if __name__ == "__main__":
    import time

    train_start = time.perf_counter()
    search_engine = SemanticTitleSearch()
    search_engine.train_engine()
    no_train_start = time.perf_counter()
    print(search_engine.get_ten_titles_indices("Third", book_id_only=False)['title'])
    end = time.perf_counter()
    print(f"Training completed in {no_train_start - train_start:.4f} seconds")
    print(f"Search completed in {end - no_train_start:.4f} seconds")