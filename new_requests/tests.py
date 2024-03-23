import unittest
import asyncio
import json

from micro_requests import fetch, get, post, put, delete

class TestHTTPClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop_policy().get_event_loop()

    async def test_fetch(self):
        response = await fetch('GET', 'https://google.com/')
        self.assertEqual(response.status_code, 200)
        # data = await response.read()
        # self.assertTrue(data)
        # response.close()

    async def test_get(self):
        result = await get('https://google.com/')
        self.assertEqual(result.status_code, 200)

    async def test_post(self):
        data = {'title': 'foo', 'body': 'bar', 'userId': 1}
        result = await post('https://google.com/', json=data)
        self.assertEqual(result.status_code, 201)
        # response_data = json.loads(await result.content())
        # self.assertEqual(response_data['title'], 'foo')

    async def test_put(self):
        data = {'title': 'foo', 'body': 'bar', 'userId': 1}
        result = await put('https://google.com/', json=data)
        self.assertEqual(result.status_code, 200)
        # response_data = json.loads(await result.content())
        # self.assertEqual(response_data['title'], 'foo')

    async def test_delete(self):
        result = await delete('https://google.com')
        self.assertEqual(result.status_code, 200)

if __name__ == '__main__':
    unittest.main()
