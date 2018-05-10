import os
import unittest
from unittest.mock import patch, Mock

import requests_mock

from august.api import API_GET_DOORBELLS_URL, Api, API_GET_LOCKS_URL, \
    API_GET_LOCK_STATUS_URL, API_LOCK_URL, API_UNLOCK_URL, API_GET_LOCK_URL, \
    API_GET_DOORBELL_URL, HEADER_AUGUST_API_KEY, HEADER_VALUE_API_KEY, \
    HEADER_USER_AGENT, HEADER_VALUE_USER_AGENT
from august.lock import LockStatus, LockDoorStatus

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
    with open(path) as fptr:
        return fptr.read()


class TestApi(unittest.TestCase):
    @requests_mock.Mocker()
    def test_get_doorbells(self, mock):
        mock.register_uri(
            "get",
            API_GET_DOORBELLS_URL,
            text=load_fixture("get_doorbells.json"))

        api = Api()
        doorbells = api.get_doorbells(ACCESS_TOKEN)

        self.assertEqual(2, len(doorbells))

        first = doorbells[0]
        self.assertEqual("K98GiDT45GUL", first.device_id)
        self.assertEqual("tBXZR0Z35E", first.serial_number)
        self.assertEqual("Front Door", first.device_name)
        self.assertEqual("doorbell_call_status_online", first.status)
        self.assertEqual(True, first.has_subscription)
        self.assertEqual("https://image.com/vmk16naaaa7ibuey7sar.jpg",
                         first.image_url)
        self.assertEqual("3dd2accaea08", first.house_id)

        second = doorbells[1]
        self.assertEqual("1KDAbJH89XYZ", second.device_id)
        self.assertEqual("aaaaR08888", second.serial_number)
        self.assertEqual("Back Door", second.device_name)
        self.assertEqual("doorbell_call_status_offline", second.status)
        self.assertEqual(False, second.has_subscription)
        self.assertEqual(None, second.image_url)
        self.assertEqual("3dd2accadddd", second.house_id)

    @requests_mock.Mocker()
    def test_get_doorbell_detail(self, mock):
        mock.register_uri(
            "get",
            API_GET_DOORBELL_URL.format(doorbell_id="K98GiDT45GUL"),
            text=load_fixture("get_doorbell.json"))

        api = Api()
        doorbell = api.get_doorbell_detail(ACCESS_TOKEN, "K98GiDT45GUL")

        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual("Front Door", doorbell.device_name)
        self.assertEqual("3dd2accaea08", doorbell.house_id)
        self.assertEqual("tBXZR0Z35E", doorbell.serial_number)
        self.assertEqual("2.3.0-RC153+201711151527", doorbell.firmware_version)
        self.assertEqual("doorbell_call_status_online", doorbell.status)
        self.assertEqual(True, doorbell.is_online)
        self.assertEqual(True, doorbell.has_subscription)
        self.assertEqual("https://image.com/vmk16naaaa7ibuey7sar.jpg",
                         doorbell.image_url)

    @requests_mock.Mocker()
    def test_get_locks(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCKS_URL,
            text=load_fixture("get_locks.json"))

        api = Api()
        locks = api.get_locks(ACCESS_TOKEN)

        self.assertEqual(2, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

        second = locks[1]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF9999", second.device_id)
        self.assertEqual("Back Door Lock", second.device_name)
        self.assertEqual("000000000011", second.house_id)
        self.assertEqual(False, second.is_operable)

    @requests_mock.Mocker()
    def test_get_operable_locks(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCKS_URL,
            text=load_fixture("get_locks.json"))

        api = Api()
        locks = api.get_operable_locks(ACCESS_TOKEN)

        self.assertEqual(1, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

    @requests_mock.Mocker()
    def test_get_lock_detail(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCK_URL.format(
                lock_id="A6697750D607098BAE8D6BAA11EF8063"),
            text=load_fixture("get_lock.json"))

        api = Api()
        lock = api.get_lock_detail(ACCESS_TOKEN,
                                   "A6697750D607098BAE8D6BAA11EF8063")

        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual("Front Door Lock", lock.device_name)
        self.assertEqual("000000000000", lock.house_id)
        self.assertEqual("X2FSW05DGA", lock.serial_number)
        self.assertEqual("109717e9-3.0.44-3.0.30", lock.firmware_version)
        self.assertEqual(88, lock.battery_level)

    @requests_mock.Mocker()
    def test_get_lock_status_with_locked_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Locked\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @requests_mock.Mocker()
    def test_get_lock_status_with_unlocked_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Unlocked\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @requests_mock.Mocker()
    def test_get_lock_status_with_unknown_status_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"not_advertising\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNKNOWN, status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_closed_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"kAugLockDoorState_Closed\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.CLOSED, door_status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_open_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"kAugLockDoorState_Open\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.OPEN, door_status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_unknown_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"not_advertising\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.UNKNOWN, door_status)

    @requests_mock.Mocker()
    def test_lock(self, mock):
        lock_id = 1234
        mock.register_uri(
            "put",
            API_LOCK_URL.format(lock_id=lock_id),
            text="{\"status\":\"locked\","
                 "\"dateTime\":\"2017-12-10T07:43:39.056Z\","
                 "\"isLockStatusChanged\":false,"
                 "\"valid\":true}")

        api = Api()
        status = api.lock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @requests_mock.Mocker()
    def test_unlock(self, mock):
        lock_id = 1234
        mock.register_uri(
            "put",
            API_UNLOCK_URL.format(lock_id=lock_id),
            text="{\"status\": \"unlocked\"}")

        api = Api()
        status = api.unlock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)


def test_passing_api_key():
    """Test passing an api key to API object."""
    api = Api()

    with patch('requests.request', return_value=Mock(json=Mock(return_value={
        'status': ''
    }))) as mock_request:
        api.lock('fake-access-token', 'fake-lock-id')

    assert len(mock_request.mock_calls) == 1
    headers = mock_request.mock_calls[0][2]['headers']
    assert headers[HEADER_AUGUST_API_KEY] == HEADER_VALUE_API_KEY

    api = Api(api_key='mock-api-key')

    with patch('requests.request', return_value=Mock(json=Mock(return_value={
        'status': ''
    }))) as mock_request:
        api.lock('fake-access-token', 'fake-lock-id')

    assert len(mock_request.mock_calls) == 1
    headers = mock_request.mock_calls[0][2]['headers']
    assert headers[HEADER_AUGUST_API_KEY] == 'mock-api-key'


def test_passing_user_agent():
    """Test passing a user agent to API object."""
    api = Api()

    with patch('requests.request', return_value=Mock(json=Mock(return_value={
        'status': ''
    }))) as mock_request:
        api.lock('fake-access-token', 'fake-lock-id')

    assert len(mock_request.mock_calls) == 1
    headers = mock_request.mock_calls[0][2]['headers']
    assert headers[HEADER_USER_AGENT] == HEADER_VALUE_USER_AGENT

    api = Api(user_agent='mock-user-agent')

    with patch('requests.request', return_value=Mock(json=Mock(return_value={
        'status': ''
    }))) as mock_request:
        api.lock('fake-access-token', 'fake-lock-id')

    assert len(mock_request.mock_calls) == 1
    headers = mock_request.mock_calls[0][2]['headers']
    assert headers[HEADER_USER_AGENT] == 'mock-user-agent'
