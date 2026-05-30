import pytest

if __name__ == '__main__':
    pytest.main(["tests/test_genai_route.py::test_get_route_aliases_genai", "-vv", "-s"])