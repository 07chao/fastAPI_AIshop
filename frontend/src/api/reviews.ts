
import axios from './axios';
import { Review, ReviewCreate } from '../types';

/**
 * 获取指定商品的所有评价
 * @param productId - 商品ID
 */
export const getReviewsForProduct = async (productId: number): Promise<Review[]> => {
  const response = await axios.get<{ review: Review[] }>(`/reviews/${productId}`);
  return response.data.review;
};

/**
 * 为商品创建一条新评价
 * @param reviewData - 评价数据
 */
export const createReview = async (reviewData: ReviewCreate): Promise<Review> => {
  const response = await axios.post<{ review: Review }>('/reviews/', reviewData);
  return response.data.review;
};
