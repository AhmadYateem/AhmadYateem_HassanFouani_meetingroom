"""
Integration tests for review workflows.
Tests complete review submission, moderation, and rating aggregation flows.
"""

import pytest
import json
from datetime import datetime, timedelta


class TestReviewSubmissionWorkflow:
    """Tests for review submission workflow."""

    def test_successful_review_submission(self, mysql_connection, created_test_user,
                                          created_test_room, sample_review_data, clean_database):
        """Test successful review submission flow."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment'],
            cleanliness_rating=sample_review_data['cleanliness_rating'],
            equipment_rating=sample_review_data['equipment_rating'],
            comfort_rating=sample_review_data['comfort_rating']
        )
        
        assert review_id is not None
        assert review_id > 0
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        
        assert review is not None
        assert review['rating'] == sample_review_data['rating']
        assert review['title'] == sample_review_data['title']
        assert review['status'] == 'approved'

    def test_review_with_user_and_room_details(self, mysql_connection, created_test_user,
                                                created_test_room, sample_review_data, clean_database):
        """Test review includes user and room details."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        
        assert review['username'] == created_test_user['username']
        assert review['room_name'] == created_test_room['name']


class TestReviewModerationWorkflow:
    """Tests for review moderation workflow."""

    def test_approve_review(self, mysql_connection, created_test_user,
                           created_test_room, sample_review_data, clean_database):
        """Test approving a review."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.update_review(
            mysql_connection,
            review_id=review_id,
            status='approved'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['status'] == 'approved'

    def test_reject_review(self, mysql_connection, created_test_user,
                          created_test_room, sample_review_data, clean_database):
        """Test rejecting a review."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.update_review(
            mysql_connection,
            review_id=review_id,
            status='rejected'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['status'] == 'rejected'


class TestFlaggingSystemWorkflow:
    """Tests for review flagging system workflow."""

    def test_flag_review(self, mysql_connection, created_test_user,
                        created_test_room, sample_review_data, clean_database):
        """Test flagging a review."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.flag_review(
            mysql_connection,
            review_id=review_id,
            flagged_by=created_test_user['id'],
            reason='Inappropriate content'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['is_flagged'] == 1

    def test_get_flagged_reviews(self, mysql_connection, created_test_user,
                                 created_test_room, sample_review_data, clean_database):
        """Test getting all flagged reviews."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        dao.flag_review(
            mysql_connection,
            review_id=review_id,
            flagged_by=created_test_user['id'],
            reason='Test flag'
        )
        
        flagged = dao.get_flagged_reviews(mysql_connection)
        
        assert len(flagged) >= 1


class TestVotingSystemWorkflow:
    """Tests for helpful/unhelpful voting workflow."""

    def test_vote_helpful(self, mysql_connection, created_test_user,
                         created_test_room, sample_review_data, clean_database):
        """Test voting review as helpful."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.vote_review(
            mysql_connection,
            review_id=review_id,
            user_id=created_test_user['id'],
            vote_type='helpful'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['helpful_count'] == 1

    def test_vote_unhelpful(self, mysql_connection, created_test_user,
                           created_test_room, sample_review_data, clean_database):
        """Test voting review as unhelpful."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.vote_review(
            mysql_connection,
            review_id=review_id,
            user_id=created_test_user['id'],
            vote_type='unhelpful'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['unhelpful_count'] == 1


class TestRatingAggregationWorkflow:
    """Tests for rating aggregation workflow."""

    def test_calculate_average_rating(self, mysql_connection, created_test_user,
                                      created_test_room, clean_database):
        """Test calculating average room rating."""
        from services.reviews import dao
        
        ratings = [5, 4, 4, 3, 4]
        
        for i, rating in enumerate(ratings):
            dao.create_review(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                booking_id=None,
                rating=rating,
                title=f'Review {i+1}',
                comment='Test comment'
            )
        
        avg_rating = dao.get_room_average_rating(mysql_connection, created_test_room['id'])
        
        expected_avg = sum(ratings) / len(ratings)
        assert abs(avg_rating - expected_avg) < 0.1

    def test_get_rating_distribution(self, mysql_connection, created_test_user,
                                     created_test_room, clean_database):
        """Test getting rating distribution."""
        from services.reviews import dao
        
        ratings = [5, 5, 4, 4, 4, 3, 2]
        
        for i, rating in enumerate(ratings):
            dao.create_review(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                booking_id=None,
                rating=rating,
                title=f'Review {i+1}',
                comment='Test comment'
            )
        
        distribution = dao.get_rating_distribution(mysql_connection, created_test_room['id'])
        
        assert distribution[5] == 2
        assert distribution[4] == 3
        assert distribution[3] == 1
        assert distribution[2] == 1

    def test_get_room_reviews(self, mysql_connection, created_test_user,
                              created_test_room, sample_review_data, clean_database):
        """Test getting all reviews for a room."""
        from services.reviews import dao
        
        for i in range(5):
            dao.create_review(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                booking_id=None,
                rating=sample_review_data['rating'],
                title=f'Review {i+1}',
                comment=sample_review_data['comment']
            )
        
        reviews = dao.get_room_reviews(mysql_connection, created_test_room['id'])
        
        assert len(reviews) == 5

    def test_reviews_sorted_by_date(self, mysql_connection, created_test_user,
                                    created_test_room, sample_review_data, clean_database):
        """Test reviews sorted by creation date."""
        from services.reviews import dao
        
        for i in range(3):
            dao.create_review(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                booking_id=None,
                rating=sample_review_data['rating'],
                title=f'Review {i+1}',
                comment=sample_review_data['comment']
            )
        
        reviews = dao.get_room_reviews(mysql_connection, created_test_room['id'])
        
        for i in range(len(reviews) - 1):
            assert reviews[i]['created_at'] >= reviews[i+1]['created_at']


class TestUserReviewsWorkflow:
    """Tests for user reviews workflow."""

    def test_get_user_reviews(self, mysql_connection, created_test_user,
                              created_test_room, sample_review_data, clean_database):
        """Test getting all reviews by a user."""
        from services.reviews import dao
        
        for i in range(3):
            dao.create_review(
                mysql_connection,
                user_id=created_test_user['id'],
                room_id=created_test_room['id'],
                booking_id=None,
                rating=sample_review_data['rating'],
                title=f'Review {i+1}',
                comment=sample_review_data['comment']
            )
        
        user_reviews = dao.get_user_reviews(mysql_connection, created_test_user['id'])
        
        assert len(user_reviews) == 3

    def test_delete_review(self, mysql_connection, created_test_user,
                          created_test_room, sample_review_data, clean_database):
        """Test deleting a review."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.delete_review(mysql_connection, review_id)
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review is None

    def test_update_review(self, mysql_connection, created_test_user,
                          created_test_room, sample_review_data, clean_database):
        """Test updating a review."""
        from services.reviews import dao
        
        review_id = dao.create_review(
            mysql_connection,
            user_id=created_test_user['id'],
            room_id=created_test_room['id'],
            booking_id=None,
            rating=sample_review_data['rating'],
            title=sample_review_data['title'],
            comment=sample_review_data['comment']
        )
        
        result = dao.update_review(
            mysql_connection,
            review_id=review_id,
            rating=5,
            title='Updated Title',
            comment='Updated comment'
        )
        
        assert result is True
        
        review = dao.get_review_by_id(mysql_connection, review_id)
        assert review['rating'] == 5
        assert review['title'] == 'Updated Title'
        assert review['comment'] == 'Updated comment'
