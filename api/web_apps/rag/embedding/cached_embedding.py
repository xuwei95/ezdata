from abc import ABC
from typing import List
from langchain.embeddings.base import Embeddings
from sqlalchemy.exc import IntegrityError
from web_apps import db
from web_apps.rag.db_models import Embedding
from utils.common_utils import md5, gen_uuid


class CacheEmbeddings(Embeddings, ABC):

    def __init__(self, embeddings):
        self.embeddings = embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""

        # use doc embedding cache or store if not exists
        text_embeddings_0 = []
        embedding_queue_texts = []

        status = []  # 0-has cache 1-has no cache
        for text in texts:
            hash = md5(text)
            embedding = db.session.query(Embedding).filter_by(hash=hash).first()
            if embedding:
                text_embeddings_0.append(embedding.get_embedding())
                status.append(0)
            else:
                embedding_queue_texts.append(text)
                status.append(1)

        text_embeddings_1 = self.embeddings.embed_documents(embedding_queue_texts) if embedding_queue_texts != [] else []

        i = 0
        for text in embedding_queue_texts:
            hash = md5(text)

            try:
                embedding = Embedding(id=gen_uuid(), hash=hash)
                embedding.set_embedding(text_embeddings_1[i])
                db.session.add(embedding)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                continue
            except:
                print('Failed to add embedding to db')
                continue

            i += 1

        text_embeddings = []

        for s in status:
            if s == 0:
                text_embeddings.append(text_embeddings_0.pop(0))
            else:
                text_embeddings.append(text_embeddings_1.pop(0))

        return text_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        # use doc embedding cache or store if not exists
        hash = md5(text)
        embedding = db.session.query(Embedding).filter_by(hash=hash).first()
        if embedding:
            return embedding.get_embedding()

        embedding_results = self.embeddings.embed_query(text)

        try:
            embedding = Embedding(id=gen_uuid(), hash=hash)
            embedding.set_embedding(embedding_results)
            db.session.add(embedding)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except:
            print('Failed to add embedding to db')
        return embedding_results