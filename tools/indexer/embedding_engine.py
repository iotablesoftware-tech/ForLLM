"""
Local Embedding Engine.
Generates high-dimensional vector representations of text chunks.
Uses a zero-ops, pure-python TF-IDF vectorizer by default (with zero external dependencies)
and dynamically upgrades to Deep Neural embeddings if 'sentence-transformers' is installed.
"""

import re
import numpy as np

# Simple list of English stopwords to improve keyword vector overlap quality
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
    'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here',
    'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in',
    'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'shant', 'shent', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than',
    'that', 'thats', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these', 'they',
    'theyd', 'theyll', 'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very',
    'was', 'wasnt', 'we', 'wed', 'well', 'were', 'weve', 'werent', 'what', 'whats', 'when', 'whens', 'where', 'wheres',
    'which', 'while', 'who', 'whos', 'whom', 'why', 'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll',
    'youre', 'youve', 'your', 'yours', 'yourself', 'yourselves'
}

class LocalEmbeddingEngine:
    def __init__(self):
        self.use_neural = False
        self.model = None
        self.vocabulary = {}
        self.idf = {}
        self.dimensions = 128  # Fixed dimension size for our pure-python fallback vector

        # Try to load sentence-transformers dynamically
        try:
            from sentence_transformers import SentenceTransformer
            print("[+] Loading local sentence-transformers model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.use_neural = True
            self.dimensions = 384  # all-MiniLM-L6-v2 outputs 384 dimensions
            print("[+] Neural embedding engine active.")
        except ImportError:
            print("[-] 'sentence-transformers' not installed. Falling back to high-quality local TF-IDF vectorizer.")
            self.use_neural = False

    def tokenize(self, text):
        """
        Cleans and tokenizes text into distinct lowercase words.
        """
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        return [w for w in words if w not in STOPWORDS]

    def fit_vocabulary(self, corpus):
        """
        Fits vocabulary and computes Inverse Document Frequency (IDF) over the corpus.
        Only used in fallback TF-IDF mode.
        """
        if self.use_neural:
            return
            
        print("[*] Training local TF-IDF vocabulary on specifications...")
        doc_count = len(corpus)
        if doc_count == 0:
            return

        # Count frequencies
        word_doc_counts = {}
        all_words = set()
        
        for text in corpus:
            tokens = set(self.tokenize(text))
            for token in tokens:
                word_doc_counts[token] = word_doc_counts.get(token, 0) + 1
                all_words.add(token)

        # Build vocabulary from most frequent terms (capped at dimensions limit)
        sorted_words = sorted(all_words, key=lambda w: word_doc_counts[w], reverse=True)
        # Preserve top dimensions-1 words
        top_words = sorted_words[:self.dimensions - 1]
        
        self.vocabulary = {word: idx for idx, word in enumerate(top_words)}
        
        # Calculate IDF
        for word, count in word_doc_counts.items():
            if word in self.vocabulary:
                self.idf[word] = np.log((1 + doc_count) / (1 + count)) + 1

    def encode(self, text):
        """
        Encodes a given string into a normalized floating-point vector.
        """
        if self.use_neural:
            # Generate neural embeddings
            emb = self.model.encode(text, convert_to_numpy=True)
            # Normalize vector to length=1.0 for easy cosine similarity calculations via dot product
            norm = np.linalg.norm(emb)
            return (emb / norm).tolist() if norm > 0 else emb.tolist()

        # Pure-python fallback TF-IDF vectorizer
        vector = [0.0] * self.dimensions
        tokens = self.tokenize(text)
        if not tokens or not self.vocabulary:
            # Return zero vector if no content
            return vector

        # Compute term frequency (TF)
        tf = {}
        for t in tokens:
            if t in self.vocabulary:
                tf[t] = tf.get(t, 0) + 1

        # Compute TF-IDF weights
        for term, freq in tf.items():
            idx = self.vocabulary[term]
            vector[idx] = freq * self.idf.get(term, 1.0)

        # Normalize vector length to 1.0
        vec_arr = np.array(vector)
        norm = np.linalg.norm(vec_arr)
        if norm > 0:
            vec_arr = vec_arr / norm
            
        return vec_arr.tolist()

    def calculate_similarity(self, vec_a, vec_b):
        """
        Calculates cosine similarity between two normalized vectors via simple dot product.
        """
        return float(np.dot(vec_a, vec_b))
