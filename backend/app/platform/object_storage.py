from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    size: int


class ObjectStore:
    def put_text(self, key: str, text: str, content_type: str = "text/plain; charset=utf-8") -> StoredObject:
        raise NotImplementedError


class DisabledObjectStore(ObjectStore):
    def put_text(self, key: str, text: str, content_type: str = "text/plain; charset=utf-8") -> StoredObject:
        encoded = text.encode("utf-8")
        return StoredObject(bucket="disabled", key=key, size=len(encoded))


class MinioObjectStore(ObjectStore):
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        from minio import Minio
        from minio.error import S3Error

        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except S3Error:
            raise

    def put_text(self, key: str, text: str, content_type: str = "text/plain; charset=utf-8") -> StoredObject:
        encoded = text.encode("utf-8")
        self.client.put_object(
            self.bucket,
            key,
            BytesIO(encoded),
            length=len(encoded),
            content_type=content_type,
        )
        return StoredObject(bucket=self.bucket, key=key, size=len(encoded))


def build_object_store(
    *,
    endpoint: str | None,
    access_key: str | None,
    secret_key: str | None,
    bucket: str,
    secure: bool,
) -> ObjectStore:
    if endpoint and access_key and secret_key:
        return MinioObjectStore(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            secure=secure,
        )
    return DisabledObjectStore()
