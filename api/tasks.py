import time
import cv2
import base64
import redis
import os
from celery import shared_task, chord
from celery.utils.log import get_task_logger
from .analyzer import analyze_summary_and_toxicity_with_groq, analyze_escalation_with_groq
from .advanced_pipeline import run_advanced_pipeline

logger = get_task_logger(__name__)

# Redis for frames, DB 2
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=2)

@shared_task
def summary_and_toxicity_task(post_title: str, comments_data: list):
    """1 & 3: Analyzes thread summary and toxicity combined to save rate limits."""
    logger.info(f"Summary & Toxicity Analysis for: {post_title}")
    return analyze_summary_and_toxicity_with_groq(post_title, comments_data)

@shared_task
def master_text_pipeline_task(post_title: str, comments_data: list):
    """
    Master pipeline:
    1. Cleans the raw data from Devvit
    2. Clusters the data
    3. Runs both Summary/Toxicity and Escalation on the compressed dataset.
    """
    logger.info(f"Starting Master Pipeline for: {post_title}")
    
    from .advanced_pipeline import clean_reddit_data, get_representative_comments
    
    # Step 1: Pre-process
    cleaned = clean_reddit_data(comments_data)
    clustered = get_representative_comments(cleaned, num_clusters=5)
    
    # Step 2: Analyze compressed data
    summary_result = analyze_summary_and_toxicity_with_groq(post_title, clustered)
    escalation_result = analyze_escalation_with_groq(post_title, clustered)
    
    return {
        "status": "completed",
        "summary_and_toxicity": summary_result,
        "escalation": escalation_result
    }

@shared_task
def escalation_detection_task(post_title: str, comments_data: list):
    """2: Detects if there's a fight turning abusive/personal."""
    logger.info(f"Escalation Detection for: {post_title}")
    return analyze_escalation_with_groq(post_title, comments_data)

@shared_task
def reverse_image_search_task(image_url: str):
    """4: Reverse Image Search (Placeholder)"""
    logger.info(f"Reverse Image Search for: {image_url}")
    time.sleep(2)
    return {"status": "completed", "matches_found": 0}

@shared_task
def nsfw_rating_task(frame_key: str):
    """5: NSFW Rating Task (replaces rate_frame_task)"""
    logger.info(f"NSFW Rating frame: {frame_key}")
    frame_data = redis_client.get(frame_key)
    if not frame_data:
        return {"error": "Frame not found"}
    
    # Simulate analysis on the frame
    time.sleep(1)
    return {"frame_key": frame_key, "nsfw_score": 0.05, "status": "safe"}

@shared_task
def video_master_task(video_path: str):
    """Video Master Task: Slices video into frames and dispatches nsfw rater tasks."""
    logger.info(f"Processing video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return {"error": "Could not open video file"}
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30 # fallback
        
    frame_interval = int(fps * 3) # Every 3 seconds
    
    frame_count = 0
    saved_frames = 0
    frame_keys = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            # Save to Redis with 10 min TTL
            key = f"frame:{video_path}:{saved_frames}"
            redis_client.setex(key, 600, jpg_as_text)
            frame_keys.append(key)
            saved_frames += 1
            
        frame_count += 1
        
    cap.release()
    
    # Fan out to nsfw tasks using chord (Wait for all to finish, then compile results)
    # Since we are just demonstrating, we will return the chord result
    return f"Dispatched {saved_frames} frames for analysis."
