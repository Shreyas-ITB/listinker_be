import boto3
import uuid
from fastapi import UploadFile
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, IMAGES_BUCKET_NAME
from botocore.client import Config

class S3Client:
    def __init__(self):
        self.bucket_name = IMAGES_BUCKET_NAME
        self.endpoint_url = f"https://{AWS_REGION}.contabostorage.com"
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            endpoint_url=self.endpoint_url,
            config=Config(signature_version="s3v4")
        )

    async def upload_file(self, file: UploadFile) -> str:
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"

        try:
            await file.seek(0)
            contents = await file.read()

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=contents,
                ContentType=file.content_type or 'image/jpeg'
            )

            return f"{filename}"
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise e

    def delete_file(self, filename: str):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
        except Exception as e:
            print(f"Error deleting file: {e}")

s3_client = S3Client()
