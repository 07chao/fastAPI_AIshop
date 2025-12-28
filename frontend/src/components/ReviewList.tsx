
import React from 'react';
import { Review } from '../types';
import StarRating from './StarRating';

interface ReviewListProps {
  reviews: Review[];
}

const ReviewList: React.FC<ReviewListProps> = ({ reviews }) => {
  if (!reviews || reviews.length === 0) {
    return <p className="mt-4 text-gray-500">No reviews yet.</p>;
  }

  return (
    <div className="mt-6">
      <h3 className="text-lg font-medium text-gray-900">Customer Reviews</h3>
      <div className="mt-4 space-y-6">
        {reviews.map((review) => (
          <div key={review.id} className="border-t border-gray-200 pt-6">
            <div className="flex items-center">
              <StarRating rating={review.rating} />
              <p className="ml-2 text-sm font-medium text-gray-900">By User {review.id}</p> {/* Placeholder for username */}
            </div>
            <p className="mt-2 text-sm text-gray-600">{review.content}</p>
            <p className="mt-2 text-xs text-gray-500">{new Date(review.created_at).toLocaleDateString()}</p>
            {/* Render follow-up reviews if they exist */}
            {review.follow_up_reviews && review.follow_up_reviews.length > 0 && (
              <div className="mt-4 ml-4 pl-4 border-l-2 border-gray-200">
                {review.follow_up_reviews.map(followUp => (
                  <div key={followUp.id} className="mt-4">
                     <p className="text-sm font-medium text-gray-800">Follow-up:</p>
                     <p className="mt-1 text-sm text-gray-600">{followUp.content}</p>
                     <p className="mt-1 text-xs text-gray-500">{new Date(followUp.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReviewList;
