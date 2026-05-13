import logging
from typing import List, Dict
import numpy as np

logger = logging.getLogger(__name__)

# To run this pipeline, ensure these are in requirements.txt:
# scikit-learn
# sentence-transformers

def clean_reddit_data(comments_data: List[Dict]) -> List[Dict]:
    """
    Step 1: Programmatic Data Cleaning
    Filters out noise before touching the LLM.
    """
    cleaned = []
    ignore_keywords = ["[deleted]", "[removed]", "I am a bot", "AutoModerator"]
    
    for c in comments_data:
        body = c.get('body', '') if isinstance(c, dict) else getattr(c, 'body', '')
        
        # Strip if too short (e.g. "This.", "Following")
        if len(body.split()) < 5:
            continue
            
        # Strip boilerplate and bots
        if any(keyword in body for keyword in ignore_keywords):
            continue
            
        cleaned.append(c)
        
    logger.info(f"Cleaned data: Reduced from {len(comments_data)} to {len(cleaned)} comments.")
    return cleaned

def get_representative_comments(comments: List[Dict], num_clusters: int = 5) -> List[Dict]:
    """
    Step 3: Semantic Clustering
    Embeds comments, clusters them, and extracts the most representative comment from each cluster.
    """
    if len(comments) <= num_clusters:
        return comments
        
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import KMeans
        
        # Load a small, fast local embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        bodies = [c.get('body', '') if isinstance(c, dict) else getattr(c, 'body', '') for c in comments]
        embeddings = model.encode(bodies)
        
        # Cluster the embeddings
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(embeddings)
        
        representative_comments = []
        for i in range(num_clusters):
            # Find the comment closest to the cluster center
            center = kmeans.cluster_centers_[i]
            distances = np.linalg.norm(embeddings - center, axis=1)
            closest_idx = np.argmin(distances)
            
            rep_comment = comments[closest_idx]
            cluster_size = np.sum(kmeans.labels_ == i)
            
            # Add context for the LLM
            body = rep_comment.get('body', '') if isinstance(rep_comment, dict) else getattr(rep_comment, 'body', '')
            if isinstance(rep_comment, dict):
                rep_comment['body'] = f"[This opinion was shared by ~{cluster_size} users]: {body}"
            
            representative_comments.append(rep_comment)
            
        return representative_comments
        
    except ImportError:
        logger.warning("Clustering dependencies missing. Returning subset.")
        return comments[:num_clusters]

def map_reduce_summarize(post_title: str, clustered_comments: List[Dict], analyzer_func) -> dict:
    """
    Step 2: Map-Reduce Architecture
    Since we clustered, our Map phase is simplified. We summarize the representatives.
    If the dataset was truly massive (millions of words), we would map each cluster 
    asynchronously via Celery, but here we synthesize the clustered output.
    """
    # MAP PHASE (Simulated by formatting the clustered representatives)
    formatted_chunks = []
    for c in clustered_comments:
        c_body = c.get('body', '') if isinstance(c, dict) else getattr(c, 'body', '')
        formatted_chunks.append(c_body)
        
    # REDUCE PHASE
    # We pass the highly-dense, clustered representations to the final LLM call
    combined_text = "\n\n".join(formatted_chunks)
    
    # We reuse the existing Groq analyzer for the Reduce step
    # Wrapping it in a mock structure to match the single text input
    mock_comment = {"id": "reduce_01", "author": "Cluster_System", "body": combined_text}
    
    logger.info("Executing Reduce Phase via LLM...")
    final_summary = analyzer_func(post_title, [mock_comment])
    
    return final_summary

def run_advanced_pipeline(post_title: str, raw_comments: List[Dict], analyzer_func) -> dict:
    """
    The Ultimate Pipeline Orchestrator
    """
    # 1. Clean
    cleaned = clean_reddit_data(raw_comments)
    
    # 2. Cluster
    clustered = get_representative_comments(cleaned, num_clusters=5)
    
    # 3. Map-Reduce (Summarize)
    final_result = map_reduce_summarize(post_title, clustered, analyzer_func)
    
    return final_result
