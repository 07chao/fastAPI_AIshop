
import React, { useState } from 'react';
import { createReview } from '../api/reviews';
import { ReviewCreate } from '../types';

interface ReviewFormProps {
  productId: number;
  onReviewSubmitted: () => void; // 用于通知父组件刷新评价列表
}

const ReviewForm: React.FC<ReviewFormProps> = ({ productId, onReviewSubmitted }) => {
  const [rating, setRating] = useState(0);
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0 || content.trim() === '') {
      setError('Please provide a rating and a comment.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const reviewData: ReviewCreate = { productId, rating, content };

    try {
      await createReview(reviewData);
      setRating(0);
      setContent('');
      onReviewSubmitted(); // 触发回调
    } catch (err) {
      setError('Failed to submit review. You may have already reviewed this product or you need to purchase it first.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-6">
      <h3 className="text-lg font-medium text-gray-900">Write a review</h3>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="mt-4">
        <label htmlFor="rating" className="block text-sm font-medium text-gray-700">Rating</label>
        <div className="flex items-center">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              className={`text-2xl ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            >
              ★
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4">
        <label htmlFor="content" className="block text-sm font-medium text-gray-700">Comment</label>
        <textarea
          id="content"
          name="content"
          rows={4}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        ></textarea>
      </div>
      <div className="mt-4">
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Review'}
        </button>
      </div>
    </form>
  );
};

export default ReviewForm;
