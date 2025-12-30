import logging

from elasticsearch import AsyncElasticsearch

from app.core.config import settings

logger = logging.getLogger(__name__)

MOVIES_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase", "asciifolding"]
                },
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            },
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "movie_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "autocomplete_analyzer",
                "search_analyzer": "search_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    },
                    "suggest": {
                        "type": "completion"
                    }
                }
            },
            "original_title": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "description": {
                "type": "text",
                "analyzer": "standard"
            },
            "year": {
                "type": "integer"
            },
            "duration": {
                "type": "integer"
            },
            "rating": {
                "type": "float"
            },
            "age_rating": {
                "type": "keyword"
            },
            "is_published": {
                "type": "boolean"
            },
            "published_at": {
                "type": "date"
            },
            "poster_url": {
                "type": "keyword",
                "index": False
            },
            "trailer_url": {
                "type": "keyword",
                "index": False
            },
            "imdb_id": {
                "type": "keyword"
            },
            "genres": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "slug": {"type": "keyword"}
                }
            },
            "actors": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "character_name": {"type": "text"}
                }
            },
            "directors": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    }
                }
            },
            "created_at": {
                "type": "date"
            },
            "updated_at": {
                "type": "date"
            }
        }
    }
}


class ElasticsearchClient:
    def __init__(self):
        self.client: AsyncElasticsearch | None = None

    async def connect(self):
        try:
            self.client = AsyncElasticsearch(
                hosts=settings.ELASTICSEARCH_HOSTS,
                request_timeout=settings.ELASTICSEARCH_TIMEOUT,
                max_retries=settings.ELASTICSEARCH_MAX_RETRIES,
                retry_on_timeout=True
            )

            if await self.client.ping():
                logger.info("Connected to Elasticsearch")

                await self.ensure_index()
            else:
                logger.error("Failed to ping Elasticsearch")
        except Exception as e:
            logger.error(f"Elasticsearch connection error: {e}")
            raise

    async def ensure_index(self):
        try:
            index_exists = await self.client.indices.exists(index=settings.ELASTICSEARCH_INDEX)

            if not index_exists:
                await self.client.indices.create(
                    index=settings.ELASTICSEARCH_INDEX,
                    body=MOVIES_INDEX_MAPPING
                )
                logger.info(f"Created index: {settings.ELASTICSEARCH_INDEX}")
            else:
                logger.info(f"Index already exists: {settings.ELASTICSEARCH_INDEX}")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch connection closed")

    def get_client(self) -> AsyncElasticsearch:
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        return self.client


es_client = ElasticsearchClient()


async def get_es_client() -> AsyncElasticsearch:
    return es_client.get_client()
