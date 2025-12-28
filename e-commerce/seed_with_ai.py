import asyncio
import httpx
import os
from dotenv import load_dotenv
import random
import json
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API base URL from environment
API_BASE_URL = "http://127.0.0.1:8000"
ADMIN_TOKEN = ""   # 后面会填充

# Configure the AI client
# Make sure you have DEEPSEEK_API_KEY and DEEPSEEK_API_BASE in your .env file
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE"),
)

async def generate_product_from_ai(category: str):
    """
    Generates a single product for a given category using an AI model.
    """
    print(f"🤖 Generating AI product for category: {category}...")
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative product manager. Your task is to generate a single, realistic product in JSON format. The product must belong to the specified category. The JSON object should include 'name', 'description', 'price' (a float between 10.0 and 1000.0), 'stock' (an integer between 10 and 100), and 'promotional_price' (a float, slightly lower than the price, or null)."
                },
                {
                    "role": "user",
                    "content": f"Generate a product for the category: '{category}'"
                }
            ],
            response_format={"type": "json_object"},
            temperature=1.2,
        )
        product_data = json.loads(response.choices[0].message.content)
        print(f"✅ AI-Generated Product: {product_data.get('name')}")
        return product_data
    except Exception as e:
        print(f"❌ Error generating product from AI: {e}")
        return None

async def generate_review_from_ai(product_name: str):
    """
    Generates a product review using an AI model.
    """
    print(f"🤖 Generating AI review for product: {product_name}...")
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a customer. Your task is to write a short, realistic review for a product in JSON format. The JSON object should include 'rating' (an integer between 1 and 5) and 'comment' (a string of 15-50 words)."
                },
                {
                    "role": "user",
                    "content": f"Write a review for the product: '{product_name}'"
                }
            ],
            response_format={"type": "json_object"},
            temperature=1.4,
        )
        review_data = json.loads(response.choices[0].message.content)
        print(f"✅ AI-Generated Review: Rating {review_data.get('rating')}/5")
        return review_data
    except Exception as e:
        print(f"❌ Error generating review from AI: {e}")
        return None

async def create_product(product_data: dict, category_id: int):
    """
    Creates a product by calling the API.
    """
    product_data['category_id'] = category_id
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/products/", json=product_data)
            response.raise_for_status()  # Raise an exception for bad status codes
            created_product = response.json()
            print(f"✅ Product '{created_product.get('name')}' created successfully with ID: {created_product.get('id')}")
            return created_product
        except httpx.HTTPStatusError as e:
            print(f"❌ Error creating product: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred while creating product: {e}")
            return None

async def create_user_and_get_token():
    """
    Creates a new random user and logs them in to get an auth token.
    """
    unique_id = random.randint(10000, 99999)
    user_data = {
        "email": f"user_{unique_id}@example.com",
        "password": "password123",
        "username": f"user_{unique_id}",
        "full_name": f"Test User {unique_id}",
        "phone_number": f"138000{unique_id}"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Register user
            register_response = await client.post(f"{API_BASE_URL}/auth/register/", json=user_data)
            register_response.raise_for_status()
            print(f"✅ User '{user_data['email']}' created successfully.")

            # Login to get token
            login_data = {"username": user_data['email'], "password": user_data['password']}
            login_response = await client.post(f"{API_BASE_URL}/auth/login", data=login_data)
            login_response.raise_for_status()
            token = login_response.json().get("accessToken")
            print(f"✅ User '{user_data['email']}' logged in successfully.")
            return token
        except httpx.HTTPStatusError as e:
            print(f"❌ Error during user creation/login: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during user creation/login: {e}")
            return None

async def create_review(product_id: int, review_data: dict, token: str):
    """
    Creates a review for a product using an authenticated user token.
    """
    review_data['product_id'] = product_id
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE_URL}/reviews/", json=review_data, headers=headers)
            response.raise_for_status()
            created_review = response.json()
            print(f"✅ Review created successfully for product ID: {product_id}")
            return created_review
        except httpx.HTTPStatusError as e:
            print(f"❌ Error creating review: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred while creating review: {e}")
            return None

async def main():
    """
    Main function to run the seeding process.
    """
    categories = {
        "Electronics": 1,
        "Apparel": 2,
        "Furniture": 3,
        "Books": 4
    }
    num_products_per_category = 25
    num_reviews_per_product = (1, 2) # Randomly generate 1 or 2 reviews

    for category_name, category_id in categories.items():
        print(f"\n---\nProcessing Category: {category_name}\n---")
        for i in range(num_products_per_category):
            print(f"\n--- Generating Product {i+1}/{num_products_per_category} for {category_name} ---")
            # 1. Generate a product
            product_data = await generate_product_from_ai(category_name)
            if not product_data:
                continue

            # 2. Create the product via API
            created_product = await create_product(product_data, category_id)
            if not created_product:
                continue

            # 3. Generate and create reviews
            num_reviews = random.randint(*num_reviews_per_product)
            for j in range(num_reviews):
                print(f"--- Generating Review {j+1}/{num_reviews} for Product '{created_product.get('name')}' ---")
                # 3a. Create a new user and get their token
                auth_token = await create_user_and_get_token()
                if not auth_token:
                    continue

                # 3b. Generate a review
                review_data = await generate_review_from_ai(created_product.get('name'))
                if not review_data:
                    continue

                # 3c. Create the review via API
                await create_review(created_product.get('id'), review_data, auth_token)

if __name__ == "__main__":
    asyncio.run(main())

