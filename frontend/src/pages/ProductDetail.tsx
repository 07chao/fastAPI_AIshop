
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getProductById } from '../api/products';
import { getReviewsForProduct } from '../api/reviews';
import { Product, Review } from '../types';
import StarRating from '../components/StarRating';
import ReviewList from '../components/ReviewList';
import ReviewForm from '../components/ReviewForm';

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProductAndReviews = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const productId = parseInt(id, 10);
      const productData = await getProductById(productId);
      setProduct(productData);
      const reviewsData = await getReviewsForProduct(productId);
      setReviews(reviewsData);
    } catch (err) {
      setError('Failed to load product details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductAndReviews();
  }, [id]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!product) return <p>Product not found.</p>;

  return (
    <div className="container mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <img src={product.image_url} alt={product.name} className="w-full h-auto rounded-lg shadow-lg" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <div className="flex items-center mt-2">
            <StarRating rating={product.average_rating} />
            <span className="ml-2 text-gray-600">({product.review_count} reviews)</span>
          </div>
          <p className="text-2xl font-semibold text-gray-800 mt-4">${product.price.toFixed(2)}</p>
          <p className="mt-4 text-gray-700">{product.description}</p>
          <div className="mt-6">
            <button className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">
              Add to Cart
            </button>
          </div>
        </div>
      </div>

      <div className="mt-12">
        <ReviewList reviews={reviews} />
        <ReviewForm productId={product.id} onReviewSubmitted={fetchProductAndReviews} />
      </div>
    </div>
  );
};

export default ProductDetail;
