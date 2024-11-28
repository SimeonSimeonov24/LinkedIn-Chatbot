import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pymongo import MongoClient
import ollama
import time
import subprocess
from minio import Minio
from dotenv import load_dotenv
import os
import redis

# Database Configuration

load_dotenv()

# PostgreSQL
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

# MongoDB
MONGO_DB_USER = os.getenv("MONGO_DB_USER")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# MinIO
MINIO_HOST = os.getenv("MINIO_HOST")
MINIO_PORT = os.getenv("MINIO_PORT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")


def start_docker():
    commands = [
        #"""start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe""",
        "docker-compose down -v",
        "docker-compose up -d",
        "docker ps",
    ]

    for command in commands:
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                capture_output=True,
            )
            print(f"Command '{command}' executed successfully:")
            print(result.stdout)

            if command == commands[0]:
                print("Loading...")
                time.sleep(10)
            else:
                print("Loading...")
                time.sleep(10)

        except subprocess.CalledProcessError as e:
            print(f"Error occurred while executing '{command}':")
            print(e.stderr)
        except FileNotFoundError:
            print(f"Command not found or not executable: '{command}'")
    time.sleep(20)

def initialize_postgresql():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create the database if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{PG_DB}';")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {PG_DB};")
            print(f"Database {PG_DB} created successfully.")

        conn.close()

        # Connect to the new database and create the table
        conn = psycopg2.connect(
            dbname=PG_DB, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT
        )
        cur = conn.cursor()

        # Enable vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                embedding VECTOR(1024),
                document TEXT
            );
        """
        )
        conn.commit()
        print("PostgreSQL initialized successfully.")
        # Connect to PostgreSQL
        return conn
    except Exception as e:
        print(f"Error initializing PostgreSQL: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def initialize_mongodb():
    try:
        mongo_uri = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource={MONGO_AUTH_SOURCE}"
        client = MongoClient(mongo_uri)

        db = client[MONGO_DB]
        print("MongoDB initialized successfully.")
        return db
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")
        return None

def initialize_redis():
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    return redis_client

def initialize_minio():
    endpoint = f"{MINIO_HOST}:{MINIO_PORT}"
    
    # Initialize the Minio client
    minio_client = Minio(
        endpoint, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False
    )
    return minio_client

def truncate_context(context, max_chars):
    return context[:max_chars]

def vector_embedding_in_pg(data, pg_conn):
    try:
        pg_cur = pg_conn.cursor()

        for i, prompt in enumerate(data):
            # Generate embedding
            embedding = ollama.embeddings(model="mxbai-embed-large:latest", prompt=prompt)[
                "embedding"
            ]

            # Insert into PostgreSQL
            pg_cur.execute(
                "INSERT INTO items (embedding, document) VALUES (%s, %s);",
                (embedding, prompt),
            )
            pg_conn.commit()

        print(".")
    except Exception as e:
        print(f"Error inserting documents: {e}")
    finally:
        if pg_cur:
            pg_cur.close()


def insert_data(pg_conn, mongo_db, redis_conn, minio_conn):
    documents = ...
    try:
        pg_cur = pg_conn.cursor()
        mongo_collection = mongo_db["documents"]

        for i, doc in enumerate(documents):
            # Generate embedding
            embedding = ollama.embeddings(model="mxbai-embed-large:latest", prompt=doc)[
                "embedding"
            ]

            # Insert into PostgreSQL
            pg_cur.execute(
                "INSERT INTO items (embedding, document) VALUES (%s, %s);",
                (embedding, doc),
            )
            pg_conn.commit()

            # Insert into MongoDB
            mongo_collection.insert_one({"id": i + 1, "content": doc})

            # Insert into Redis
            # redis_conn.set()

            # Insert into MinIO

        print("Documents inserted successfully into PostgreSQL and MongoDB.")
    except Exception as e:
        print(f"Error inserting documents: {e}")
    finally:
        if pg_cur:
            pg_cur.close()


def retrieve_context(pg_conn, user_query, max_context_chars=90000):
    """
    Retrieve the most relevant context for a user query using pgvector.
    """
    try:
        pg_cur = pg_conn.cursor()
        query_embedding = ollama.embeddings(
            model="mxbai-embed-large:latest", prompt=user_query
        )["embedding"]

        pg_cur.execute(
            """
            SELECT id, document, embedding <-> %s::vector AS distance
            FROM items
            ORDER BY distance
            LIMIT 3;
        """,
            (query_embedding,),
        )
        retrieved_docs = pg_cur.fetchall()

        unique_docs = list(set([doc[1] for doc in retrieved_docs]))
        context = "\n".join(unique_docs)

        # Truncate context and debug the length
        truncated_context = truncate_context(context, max_context_chars)
        print(f"Retrieved Context Length: {len(truncated_context)}")
        return truncated_context
    except Exception as e:
        print(f"Error retrieving context: {e}")
        return "No relevant context found."
    finally:
        if pg_cur:
            pg_cur.close()


def generate_response(pg_conn, user_query, chat_history):
    """
    Generate a response for a user query by combining context and chat history.
    """
    # Retrieve the context
    context = retrieve_context(pg_conn, user_query)

    # Ensure only one system message exists
    if not any(msg["role"] == "system" for msg in chat_history):
        system_message = (
            "You are a helpful assistant knowledgeable about technology and databases. "
            "Use the context below to answer queries."
        )
        chat_history.insert(0, {"role": "system", "content": system_message})

    # Add the relevant context as its own message
    if context:
        chat_history.append(
            {"role": "system", "content": f"Relevant Context: {context}"}
        )

    # Add the user's query
    chat_history.append({"role": "user", "content": user_query})

    # Debug: Print the full chat history
    print("\n=== Chat History ===")
    for message in chat_history:
        print(f"{message['role']}: {message['content']}")
    print("====================\n")

    # Generate response
    try:
        response = ollama.chat(model="llama3.2", messages=chat_history)  # "llama3.1:8b"
        print("Chat Response:", response)

        # Extract assistant response
        assistant_response = response.get("message", {}).get("content", "").strip()
        if not assistant_response:
            assistant_response = (
                "I'm sorry, I couldn't generate a response. Please try again."
            )
    except Exception as e:
        print(f"Error during response generation: {e}")
        assistant_response = (
            "There was an error generating a response. Please try again later."
        )

    # Append assistant response to chat history
    chat_history.append({"role": "assistant", "content": assistant_response})

    return assistant_response


def main():
    # Initialize Docker
    #start_docker()

    # Initialize Databases (Postgres, MongoDB, Redis, MinIO)
    pg_conn = initialize_postgresql()
    mongo_db = initialize_mongodb()
    redis_conn = initialize_redis()
    minio_conn = initialize_minio()

    # Indexing und Aggregation

    # Vector Datenbanken
    # vector_embedding_in_pg(data, pg_conn)


    # Feynman Technique

    # Redis: In Memory Datenbank

    # LLM Chatbot mit RAG

    # Min.IO Object Storage

    
    # Insert Data
    insert_data(pg_conn, mongo_db, redis_conn, minio_conn)

    # Chatbot Interaction
    chat_history = [
        {
            "role": "system",
            "content": "You are a helpful assistant knowledgeable about technology and databases.",
        }
    ]
    print("Chatbot ready. Type your queries below:")

    while True:
        user_query = input("You: ")
        if user_query.lower() in ["exit", "quit"]:
            break

        response = generate_response(pg_conn, user_query, chat_history)
        print(f"Assistant: {response}")

    # Close connections
    pg_conn.close()


if __name__ == "__main__":
    main()
