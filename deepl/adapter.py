import json
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Union

import aiohttp
import requests

from .errors import (BadRequest, Forbidden, HTTPException, InternalServerError,
                     NotFound, PayloadTooLarge, QuotaExceeded,
                     ServiceUnavailable, TooManyRequests, URITooLong)


class Adapter(metaclass=ABCMeta):
    def __init__(self, authentication_key: str, *, pro: bool = False) -> None:
        self.base_url_free = 'https://api-free.deepl.com/'
        self.base_url_pro = 'https://api.deepl.com/'
        self.api_version = 'v2'
        self.auth_key = authentication_key
        self.pro = pro

    @abstractmethod
    def request(self, method: str,
                path: str, payload: dict = {}, **kwargs) -> Optional[Union[list, dict]]:
        raise NotImplementedError()

    @abstractmethod
    def get_translated_text(self, payload: dict) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_usage(self) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def get_supported_languages(self) -> List[dict]:
        raise NotImplementedError()


class RequestsAdapter(Adapter):
    def request(self, method: str,
                path: str, payload: dict = {}, **kwargs) -> Optional[Union[list, dict]]:
        headers = {'content-type': 'x-www-form-urlencoded'}
        payload['auth_key'] = self.auth_key

        url = self.base_url_pro if self.pro else self.base_url_free
        url += self.api_version + path

        resp = requests.request(method, url, params=payload, headers=headers, **kwargs)
        try:
            data = resp.json()
        except json.JSONDecodeError:
            data = None
        status_code = resp.status_code
        if 200 <= status_code < 300:
            return data
        message = data.get('message', '') if data else ''
        if status_code == 400:
            raise BadRequest(resp, message)
        elif status_code == 403:
            raise Forbidden(resp, message)
        elif status_code == 404:
            raise NotFound(resp, message)
        elif status_code == 413:
            raise PayloadTooLarge(resp, message)
        elif status_code == 414:
            raise URITooLong(resp, message)
        elif status_code == 429:
            raise TooManyRequests(resp, message)
        elif status_code == 456:
            raise QuotaExceeded(resp, message)
        elif status_code == 503:
            raise ServiceUnavailable(resp, message)
        elif 500 <= status_code < 600:
            raise InternalServerError(resp, message)
        else:
            raise HTTPException(resp, message)

    def get_translated_text(self, payload) -> str:
        data = self.request('POST', '/translate', payload)
        return data['translations'][0]['text']

    def get_usage(self) -> dict:
        data = self.request('POST', '/usage')
        return data

    def get_supported_languages(self) -> List[dict]:
        data = self.request('POST', '/languages')
        return data


class AiohttpAdapter(Adapter):

    async def request(self, method: str,
                      path: str, payload: dict = {}, **kwargs) -> Optional[Union[list, dict]]:
        headers = {'content-type': 'x-www-form-urlencoded'}
        payload['auth_key'] = self.auth_key

        url = self.base_url_pro if self.pro else self.base_url_free
        url += self.api_version + path

        async with aiohttp.request(
                method, url, params=payload, headers=headers, **kwargs) as resp:
            try:
                data = await resp.json(content_type=None)
            except json.JSONDecodeError:
                data = None
            status_code = resp.status
            if 200 <= status_code < 300:
                return data
            message = data.get('message', '') if data else ''
            if status_code == 400:
                raise BadRequest(resp, message)
            elif status_code == 403:
                raise Forbidden(resp, message)
            elif status_code == 404:
                raise NotFound(resp, message)
            elif status_code == 413:
                raise PayloadTooLarge(resp, message)
            elif status_code == 414:
                raise URITooLong(resp, message)
            elif status_code == 429:
                raise TooManyRequests(resp, message)
            elif status_code == 456:
                raise QuotaExceeded(resp, message)
            elif status_code == 503:
                raise ServiceUnavailable(resp, message)
            elif 500 <= status_code < 600:
                raise InternalServerError(resp, message)
            else:
                raise HTTPException(resp, message)

    async def get_translated_text(self, payload: dict) -> str:
        data = await self.request('POST', '/translate', payload)
        return data['translations'][0]['text']

    async def get_usage(self) -> dict:
        data = await self.request('POST', '/usage')
        return data

    async def get_supported_languages(self) -> List[dict]:
        data = await self.request('POST', '/languages')
        return data
