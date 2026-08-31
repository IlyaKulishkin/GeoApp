from typing import Optional
from dadata import Dadata
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DadataService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DADATA_TOKEN
        if not self.api_key:
            raise ValueError("DADATA_TOKEN не установлен в настройках")

    def get_address_by_coordinates(
        self,
        lat: float,
        lon: float,
        radius_meters: int = 100
    ) -> Optional[str]:
        with Dadata(self.api_key) as dadata:
            try:
                result = dadata.geolocate(
                    name="address",
                    lat=lat,
                    lon=lon,
                    radius_meters=radius_meters
                )

                if result and result[0]:
                    address = result[0]['unrestricted_value']
                    logger.info(f"DaData: адрес для ({lat}, {lon}) → {address}")
                    return address
                else:
                    logger.warning(f"DaData: адрес не найден для ({lat}, {lon})")
                    return None

            except Exception as exc:
                logger.error(f"Ошибка DaData API для ({lat}, {lon}): {exc}")
                raise