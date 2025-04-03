import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class ContentBasedRecommender:
    def __init__(self) -> None:
        self.df = None
        self.cosine_sim = None
        self.indices = None
        
    def load_dataset(self, filepath='./movies_metadata.csv'):
        self.df = pd.read_csv(filepath, low_memory=False)
        self.df = self.df[['id', 'title', 'overview', 'genres']].drop_duplicates(subset=['title'])
        self.df['overview'] = self.df['overview'].fillna('')
        print(f"Loaded dataset with {len(self.df)} movies")
        
    def calculate_cosine_sim(self):
        print("Calculating cosine similarity matrix...")
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(self.df['overview'])
        print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
        
        self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        print(f"Cosine similarity matrix shape: {self.cosine_sim.shape}")
        
        self.indices = pd.Series(self.df.index, index=self.df['title'])
        self.indices = self.indices[~self.indices.index.duplicated(keep='last')]
        
    def get_recommendations(self, title, top_n=10):
        try:
            idx = self.indices[title]
            sim_scores = list(enumerate(self.cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:top_n+1]
            movie_indices = [i[0] for i in sim_scores]
            return self.df['title'].iloc[movie_indices].tolist()
        except KeyError:
            print(f"Movie '{title}' not found in the dataset")
            return []
    
    def build_recommendation_dict(self, sample_size=None):
        print("Building recommendation dictionary...")
        recommendations = {}
        
        all_titles = self.df['title'].unique()
        if sample_size and sample_size < len(all_titles):
            titles_to_process = np.random.choice(all_titles, size=sample_size, replace=False)
        else:
            titles_to_process = all_titles
        
        total = len(titles_to_process)
        for i, title in enumerate(titles_to_process):
            if i % 1000 == 0:
                print(f"Processing movie {i}/{total}...")
            recommendations[title] = self.get_recommendations(title)
        
        print(f"Generated recommendations for {len(recommendations)} movies")
        return recommendations
    
    def save_recommendations(self, output_file="rec_model"):
        recommendations = self.build_recommendation_dict()
        
        with open(output_file, "wb") as file:
            pickle.dump(recommendations, file)
        print(f"Recommendations saved to {output_file}")

def train_and_save_model(csv_path='./movies_metadata.csv', output_file="rec_model"):
    recommender = ContentBasedRecommender()
    recommender.load_dataset(csv_path)
    recommender.calculate_cosine_sim()
    recommender.save_recommendations(output_file)
    
    return recommender

if __name__ == '__main__':
    print("Content-Based Movie Recommender System")
    train_and_save_model()
    print("\nModel training complete!")
