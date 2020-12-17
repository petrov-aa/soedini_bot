import base64

from .client import get_client


PHOTO_KEY_PREFIX = 'image'


def get_image(image_id: str):
    client = get_client()
    value = client.get(PHOTO_KEY_PREFIX + image_id)
    if value is not None:
        try:
            return base64.b64decode(value.decode('utf-8'))
        except:
            pass
    return None


def store_image(image_id: str, data: bytes):
    client = get_client()
    encoded = base64.b64encode(data)
    client.set(PHOTO_KEY_PREFIX + image_id, encoded)
