import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.work import Work
from app.models.similarity import SimilarityCandidate
from app.services.geo_utils import haversine_distance

class SimilarityService:
    @staticmethod
    def compute_pair_similarity(w1: Work, w2: Work, text_sim: float = 0.0) -> Tuple[float, Dict[str, float]]:
        # 1. Text Similarity (30%)
        score_t = text_sim

        # 2. Geographic Proximity (25%)
        if w1.latitude and w1.longitude and w2.latitude and w2.longitude:
            dist_km = haversine_distance(float(w1.latitude), float(w1.longitude), float(w2.latitude), float(w2.longitude))
            score_g = max(0.0, 1.0 - (dist_km / 5.0))  # 1.0 at 0km, 0.0 at 5km+
        elif w1.location_text and w2.location_text and w1.location_text.strip().lower() == w2.location_text.strip().lower():
            score_g = 0.9
        else:
            score_g = 0.0

        # 3. Category Match (15%)
        score_c = 1.0 if (w1.category and w2.category and w1.category.strip().lower() == w2.category.strip().lower()) else 0.0

        # 4. Agency Match (10%)
        score_a = 1.0 if (w1.agency_id and w2.agency_id and w1.agency_id == w2.agency_id) else 0.0

        # 5. Cost Delta Similarity (10%)
        c1 = float(w1.sanction_amount or w1.estimated_cost or 0)
        c2 = float(w2.sanction_amount or w2.estimated_cost or 0)
        if c1 > 0 and c2 > 0:
            score_k = max(0.0, 1.0 - (abs(c1 - c2) / max(c1, c2)))
        else:
            score_k = 0.0

        # 6. Date Window Overlap (10%)
        d1 = w1.sanction_date or w1.recommendation_date
        d2 = w2.sanction_date or w2.recommendation_date
        if d1 and d2:
            days_diff = abs((d1 - d2).days)
            score_d = max(0.0, 1.0 - (days_diff / 180.0))  # 1.0 within same day, 0.0 at 180 days+
        else:
            score_d = 0.0

        # Weighted Total (0.0 to 100.0)
        total_score = (0.30 * score_t +
                       0.25 * score_g +
                       0.15 * score_c +
                       0.10 * score_a +
                       0.10 * score_k +
                       0.10 * score_d) * 100.0

        breakdown = {
            "textSimilarity": round(score_t * 100.0, 1),
            "geoProximity": round(score_g * 100.0, 1),
            "categoryMatch": round(score_c * 100.0, 1),
            "agencyMatch": round(score_a * 100.0, 1),
            "costSimilarity": round(score_k * 100.0, 1),
            "dateOverlap": round(score_d * 100.0, 1)
        }

        return round(total_score, 1), breakdown

    @staticmethod
    def get_candidate_label(score: float) -> str:
        if score >= 80.0:
            return "POSSIBLE_DUPLICATE"
        elif score >= 65.0:
            return "SIMILAR_WORK"
        else:
            return "REVIEW_CANDIDATE"

    @staticmethod
    def recompute_all_similarities(db: Session):
        works = db.query(Work).all()
        if len(works) < 2:
            return

        # Prepare TF-IDF matrix over combined title + description
        corpus = [f"{w.title} {w.description or ''} {w.location_text or ''}" for w in works]
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim_matrix = cosine_similarity(tfidf_matrix)

        # Clear existing similarity candidates
        db.query(SimilarityCandidate).delete()
        db.commit()

        n = len(works)
        for i in range(n):
            for j in range(i + 1, n):
                w1 = works[i]
                w2 = works[j]

                # Blocking filter: compare if same jurisdiction OR same category
                if w1.jurisdiction_id == w2.jurisdiction_id or w1.category == w2.category:
                    text_sim = float(cosine_sim_matrix[i, j])
                    total_score, breakdown = SimilarityService.compute_pair_similarity(w1, w2, text_sim)

                    # Store if similarity score >= 45%
                    if total_score >= 45.0:
                        label = SimilarityService.get_candidate_label(total_score)
                        
                        # Store candidate entry from w1 -> w2
                        db.add(SimilarityCandidate(
                            work_id=w1.id,
                            candidate_work_id=w2.id,
                            similarity_score=total_score,
                            candidate_label=label,
                            feature_breakdown_json=breakdown,
                            algorithm_version="sim-v1.0"
                        ))
                        # Store reverse candidate entry from w2 -> w1
                        db.add(SimilarityCandidate(
                            work_id=w2.id,
                            candidate_work_id=w1.id,
                            similarity_score=total_score,
                            candidate_label=label,
                            feature_breakdown_json=breakdown,
                            algorithm_version="sim-v1.0"
                        ))
        db.commit()

    @staticmethod
    def get_similar_works(db: Session, work_id: str) -> List[Dict[str, Any]]:
        # Check if similarity candidates exist in DB
        candidates = db.query(SimilarityCandidate).options(
            joinedload(SimilarityCandidate.candidate_work).joinedload(Work.agency),
            joinedload(SimilarityCandidate.candidate_work).joinedload(Work.jurisdiction)
        ).filter(SimilarityCandidate.work_id == work_id).order_by(desc(SimilarityCandidate.similarity_score)).all()

        if not candidates:
            # Run initial computation
            SimilarityService.recompute_all_similarities(db)
            candidates = db.query(SimilarityCandidate).options(
                joinedload(SimilarityCandidate.candidate_work).joinedload(Work.agency),
                joinedload(SimilarityCandidate.candidate_work).joinedload(Work.jurisdiction)
            ).filter(SimilarityCandidate.work_id == work_id).order_by(desc(SimilarityCandidate.similarity_score)).all()

        items = []
        for c in candidates:
            cand_work = c.candidate_work
            items.append({
                "candidateId": c.id,
                "candidateWorkId": cand_work.id,
                "workId": cand_work.id,
                "externalId": cand_work.external_id,
                "title": cand_work.title,
                "category": cand_work.category,
                "locationText": cand_work.location_text,
                "stage": cand_work.current_status,
                "sanctionAmount": float(cand_work.sanction_amount) if cand_work.sanction_amount else None,
                "similarityScore": float(c.similarity_score),
                "candidateLabel": c.candidate_label,
                "featureBreakdown": c.feature_breakdown_json,
                "agencyName": cand_work.agency.name if cand_work.agency else "Unassigned",
                "jurisdiction": {
                    "id": cand_work.jurisdiction.id,
                    "districtName": cand_work.jurisdiction.district_name,
                    "districtCode": cand_work.jurisdiction.district_code
                }
            })

        return items
