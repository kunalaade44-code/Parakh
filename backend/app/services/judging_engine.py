import json
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Project, Score, Criterion, Event
from app.schemas.schemas import ProjectResult

def calculate_project_results(db: Session, event_id: str) -> List[Dict[str, Any]]:
    """
    Computes Raw, Z-Score Standardized, and Min-Max normalized scores for all projects in an event.
    Handles harsh vs lenient judges gracefully.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    criteria_db = db.query(Criterion).filter(Criterion.event_id == event_id).all() if event else []
    
    # Map weights
    weight_map = {c.name.lower(): c.weight for c in criteria_db}
    if not weight_map:
        # Default weights
        weight_map = {"functionality": 0.35, "quality": 0.35, "innovation": 0.30}
    
    # Normalize weights sum to 1.0
    total_w = sum(weight_map.values()) or 1.0
    weight_map = {k: v / total_w for k, v in weight_map.items()}

    projects = db.query(Project).all()
    all_scores = db.query(Score).all()

    # Calculate weighted score per review
    # score_records: judge_id -> list of {project_id, weighted_score}
    judge_ratings: Dict[str, List[Dict[str, Any]]] = {}
    for s in all_scores:
        try:
            crit = json.loads(s.criteria_scores) if isinstance(s.criteria_scores, str) else s.criteria_scores
        except Exception:
            crit = {}
        
        weighted_sum = 0.0
        used_w = 0.0
        for k, val in crit.items():
            k_low = k.lower()
            w = weight_map.get(k_low, 0.25)
            weighted_sum += float(val) * w
            used_w += w
        
        rating = weighted_sum / used_w if used_w > 0 else 3.0
        
        if s.judge_id not in judge_ratings:
            judge_ratings[s.judge_id] = []
        judge_ratings[s.judge_id].append({
            "project_id": s.project_id,
            "score": rating
        })

    # Compute per-judge mean and standard deviation for Z-score normalization
    judge_stats = {}
    for j_id, ratings in judge_ratings.items():
        arr = [r["score"] for r in ratings]
        mean = float(np.mean(arr)) if len(arr) > 0 else 3.0
        std = float(np.std(arr)) if len(arr) > 1 else 0.0
        min_v = float(np.min(arr)) if len(arr) > 0 else 1.0
        max_v = float(np.max(arr)) if len(arr) > 0 else 5.0
        judge_stats[j_id] = {
            "mean": mean,
            "std": std if std > 1e-4 else 1.0, # avoid div by zero
            "min": min_v,
            "max": max_v if max_v > min_v else min_v + 1.0
        }

    # Now aggregate scores per project
    project_scores: Dict[str, Dict[str, Any]] = {}
    for p in projects:
        project_scores[p.id] = {
            "project": p,
            "raw_scores": [],
            "z_scores": [],
            "min_max_scores": []
        }

    for j_id, ratings in judge_ratings.items():
        stats = judge_stats[j_id]
        for r in ratings:
            p_id = r["project_id"]
            if p_id in project_scores:
                score_val = r["score"]
                project_scores[p_id]["raw_scores"].append(score_val)
                
                # Z-score normalization scaled back to standard 1-5 scale: 3.0 + z * 0.8
                z = (score_val - stats["mean"]) / stats["std"]
                scaled_z = np.clip(3.0 + z * 0.8, 1.0, 5.0)
                project_scores[p_id]["z_scores"].append(float(scaled_z))
                
                # Min-max normalization mapped to 1-5
                mm = 1.0 + 4.0 * ((score_val - stats["min"]) / (stats["max"] - stats["min"]))
                project_scores[p_id]["min_max_scores"].append(float(mm))

    results = []
    for p_id, data in project_scores.items():
        p = data["project"]
        raw_list = data["raw_scores"]
        z_list = data["z_scores"]
        mm_list = data["min_max_scores"]
        
        raw_avg = float(np.mean(raw_list)) if raw_list else 0.0
        z_avg = float(np.mean(z_list)) if z_list else 0.0
        mm_avg = float(np.mean(mm_list)) if mm_list else 0.0
        
        # Blended final score (70% Z-score normalized + 30% Raw)
        final_score = (0.7 * z_avg + 0.3 * raw_avg) if raw_list else 0.0

        results.append({
            "project_id": p.id,
            "title": p.title,
            "team_name": p.team.name if p.team else "No Team",
            "track_name": p.track.name if p.track else "General",
            "repo_url": p.repo_url or "",
            "submitted_at": p.submitted_at,
            "raw_avg_score": round(raw_avg, 3),
            "z_score_normalized": round(z_avg, 3),
            "min_max_normalized": round(mm_avg, 3),
            "final_score": round(final_score, 3),
            "reviews_count": len(raw_list),
            "community_votes": len(p.votes) if p.votes else 0
        })

    # Sort descending by final score
    results.sort(key=lambda x: x["final_score"], reverse=True)
    for idx, r in enumerate(results):
        r["rank"] = idx + 1

    return results
