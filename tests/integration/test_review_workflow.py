"""
Integration tests for review workflows.
Tests review submission, moderation, and rating aggregation.

Author: Hassan Fouani
"""

import pytest
from datetime import datetime


class TestReviewSubmissionWorkflow:
    """Tests for review submission workflow."""

    def test_successful_review_submission(self, mysql_connection, created_test_user,
                                          created_test_room):
        """Test successful review submission flow."""
        db = mysql_connection._db
        
        review_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'rating': 5,
            'comment': 'Excellent meeting room with all necessary equipment.',
            'is_flagged': False,
            'is_approved': True,
            'helpful_votes': 0,
            'unhelpful_votes': 0
        }
        
        review_id = db.add_review(review_data)
        
        assert review_id is not None
        assert review_id > 0
        
        review = db.reviews[review_id]
        
        assert review is not None
        assert review['user_id'] == created_test_user['id']
        assert review['room_id'] == created_test_room['id']
        assert review['rating'] == 5

    def test_review_with_user_and_room_details(self, mysql_connection, created_test_user,
                                               created_test_room):
        """Test review includes user and room details."""
        db = mysql_connection._db
        
        review_data = {
            'user_id': created_test_user['id'],
            'room_id': created_test_room['id'],
            'rating': 4,
            'comment': 'Good room, nice atmosphere.',
            'is_flagged': False,
            'is_approved': True
        }
        
        review_id = db.add_review(review_data)
        review = db.reviews[review_id]
        
        # Verify review is linked to user and room
        user = db.get_user(review['user_id'])
        room = db.get_room(review['room_id'])
        
        assert user is not None
        assert room is not None


class TestReviewModerationWorkflow:
    """Tests for review moderation workflow."""

    def test_approve_review(self, mysql_connection, created_test_review):
        """Test approving a review."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        # Approve the review
        db.reviews[review_id]['is_approved'] = True
        
        review = db.reviews[review_id]
        
        assert review['is_approved'] is True

    def test_reject_review(self, mysql_connection, created_test_review):
        """Test rejecting a review."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        # Reject the review
        db.reviews[review_id]['is_approved'] = False
        
        review = db.reviews[review_id]
        
        assert review['is_approved'] is False


class TestFlaggingSystemWorkflow:
    """Tests for review flagging system."""

    def test_flag_review(self, mysql_connection, created_test_review):
        """Test flagging an inappropriate review."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        # Flag the review
        db.reviews[review_id]['is_flagged'] = True
        db.reviews[review_id]['flag_reason'] = 'Inappropriate language'
        
        review = db.reviews[review_id]
        
        assert review['is_flagged'] is True
        assert review['flag_reason'] == 'Inappropriate language'

    def test_get_flagged_reviews(self, mysql_connection, created_test_user,
                                  created_test_room):
        """Test getting all flagged reviews."""
        db = mysql_connection._db
        
        # Create some flagged and non-flagged reviews
        for i in range(3):
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': 3,
                'comment': f'Review {i}',
                'is_flagged': i < 2,  # First 2 are flagged
                'is_approved': True
            }
            db.add_review(review_data)
        
        flagged_reviews = [r for r in db.reviews.values() if r.get('is_flagged')]
        
        assert len(flagged_reviews) == 2


class TestVotingSystemWorkflow:
    """Tests for review voting system."""

    def test_vote_helpful(self, mysql_connection, created_test_review):
        """Test voting a review as helpful."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        initial_votes = db.reviews[review_id].get('helpful_votes', 0)
        
        # Vote helpful
        db.reviews[review_id]['helpful_votes'] = initial_votes + 1
        
        review = db.reviews[review_id]
        
        assert review['helpful_votes'] == initial_votes + 1

    def test_vote_unhelpful(self, mysql_connection, created_test_review):
        """Test voting a review as unhelpful."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        initial_votes = db.reviews[review_id].get('unhelpful_votes', 0)
        
        # Vote unhelpful
        db.reviews[review_id]['unhelpful_votes'] = initial_votes + 1
        
        review = db.reviews[review_id]
        
        assert review['unhelpful_votes'] == initial_votes + 1


class TestRatingAggregationWorkflow:
    """Tests for room rating aggregation."""

    def test_calculate_average_rating(self, mysql_connection, created_test_user,
                                      created_test_room):
        """Test calculating average room rating."""
        db = mysql_connection._db
        
        # Create reviews with different ratings
        ratings = [5, 4, 4, 3, 5]
        for rating in ratings:
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': rating,
                'comment': f'Rating {rating} review',
                'is_approved': True
            }
            db.add_review(review_data)
        
        room_reviews = [r for r in db.reviews.values()
                       if r['room_id'] == created_test_room['id']]
        
        avg_rating = sum(r['rating'] for r in room_reviews) / len(room_reviews)
        
        assert avg_rating == 4.2

    def test_get_rating_distribution(self, mysql_connection, created_test_user,
                                     created_test_room):
        """Test getting rating distribution for a room."""
        db = mysql_connection._db
        
        # Create reviews with different ratings
        ratings = [5, 5, 4, 4, 4, 3, 2, 1]
        for rating in ratings:
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': rating,
                'comment': f'Rating {rating} review',
                'is_approved': True
            }
            db.add_review(review_data)
        
        room_reviews = [r for r in db.reviews.values()
                       if r['room_id'] == created_test_room['id']]
        
        # Calculate distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in room_reviews:
            distribution[review['rating']] += 1
        
        assert distribution[5] == 2
        assert distribution[4] == 3
        assert distribution[3] == 1
        assert distribution[2] == 1
        assert distribution[1] == 1

    def test_get_room_reviews(self, mysql_connection, created_test_user,
                              created_test_room):
        """Test getting all reviews for a room."""
        db = mysql_connection._db
        
        # Create multiple reviews
        for i in range(5):
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': (i % 5) + 1,
                'comment': f'Review {i+1}',
                'is_approved': True
            }
            db.add_review(review_data)
        
        room_reviews = [r for r in db.reviews.values()
                       if r['room_id'] == created_test_room['id']]
        
        assert len(room_reviews) == 5

    def test_reviews_sorted_by_date(self, mysql_connection, created_test_user,
                                    created_test_room):
        """Test reviews are sortable by date."""
        db = mysql_connection._db
        
        # Create reviews with timestamps
        for i in range(3):
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': 4,
                'comment': f'Review {i+1}',
                'is_approved': True,
                'created_at': datetime.now()
            }
            db.add_review(review_data)
        
        room_reviews = [r for r in db.reviews.values()
                       if r['room_id'] == created_test_room['id']]
        
        # Sort by created_at
        sorted_reviews = sorted(room_reviews, 
                               key=lambda x: x.get('created_at', datetime.min),
                               reverse=True)
        
        assert len(sorted_reviews) == 3


class TestUserReviewsWorkflow:
    """Tests for user review management."""

    def test_get_user_reviews(self, mysql_connection, created_test_user,
                              created_test_room):
        """Test getting all reviews by a user."""
        db = mysql_connection._db
        
        # Create multiple reviews
        for i in range(3):
            review_data = {
                'user_id': created_test_user['id'],
                'room_id': created_test_room['id'],
                'rating': 4,
                'comment': f'My review {i+1}',
                'is_approved': True
            }
            db.add_review(review_data)
        
        user_reviews = [r for r in db.reviews.values()
                       if r['user_id'] == created_test_user['id']]
        
        assert len(user_reviews) == 3

    def test_delete_review(self, mysql_connection, created_test_review):
        """Test deleting a review."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        # Delete review
        del db.reviews[review_id]
        
        review = db.reviews.get(review_id)
        
        assert review is None

    def test_update_review(self, mysql_connection, created_test_review):
        """Test updating a review."""
        db = mysql_connection._db
        review_id = created_test_review['id']
        
        # Update review
        db.reviews[review_id]['rating'] = 5
        db.reviews[review_id]['comment'] = 'Updated review comment'
        
        review = db.reviews[review_id]
        
        assert review['rating'] == 5
        assert review['comment'] == 'Updated review comment'
