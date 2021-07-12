# This file is a part of IntelOwl https://github.com/intelowlproject/IntelOwl
# See the file 'LICENSE' for copying permission.

from tests.mock_utils import patch, if_mock

from api_app.analyzers_manager.classes import ObservableAnalyzer


@if_mock(
    [
        patch(
            "darksearch.Client.search",
            side_effect=lambda *args, **kwargs: [
                {"total": 1, "last_page": 0, "data": ["test"]}
            ],
        )
    ]
)
class DarkSearchQuery(ObservableAnalyzer):
    def set_params(self, params):
        self.num_pages = int(params.get("pages", 5))
        self.proxies = params.get("proxies", None)

    def run(self):
        from darksearch import Client

        c = Client(proxies=self.proxies)
        responses = c.search(self.observable_name, pages=self.num_pages)
        result = {
            "total": responses[0]["total"],
            "total_pages": responses[0]["last_page"],
            "requested_pages": self.num_pages,
            "data": [],
        }
        for resp in responses:
            result["data"].extend(resp["data"])

        return result
