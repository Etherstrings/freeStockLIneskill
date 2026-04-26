import sys

from freestocklineskill_runtime.routing import entity_from_symbol
from freestocklineskill_runtime.sources import SourceClient
from freestocklineskill_runtime.sources import _extract_board_name
from freestocklineskill_runtime.sources import _quiet_call


class FakeResponse:
    def __init__(self, content=b"", json_payload=None, status_code=200):
        self.content = content
        self._json_payload = json_payload
        self.status_code = status_code

    def json(self):
        return self._json_payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http %s" % self.status_code)


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.trust_env = False
        self.requests = []
        self.responses = []

    def queue(self, response):
        self.responses.append(response)

    def get(self, url, params=None, headers=None, timeout=None):
        self.requests.append({"method": "GET", "url": url, "params": params, "headers": headers, "timeout": timeout})
        if not self.responses:
            raise AssertionError("no queued response")
        return self.responses.pop(0)

    def post(self, url, data=None, headers=None, timeout=None):
        self.requests.append({"method": "POST", "url": url, "data": data, "headers": headers, "timeout": timeout})
        if not self.responses:
            raise AssertionError("no queued response")
        return self.responses.pop(0)


def make_client(session):
    client = SourceClient()
    client.session = session
    return client


def test_tencent_search_entity_parses_candidate():
    session = FakeSession()
    session.queue(FakeResponse(content='v_hint="sh~600519~\\u8d35\\u5dde\\u8305\\u53f0~gzmt~GP-A"'.encode("utf-8")))
    client = make_client(session)

    result = client.search_entity("贵州茅台")

    entity = result["entity"]
    assert entity.symbol == "600519.SH"
    assert entity.name == "贵州茅台"
    assert result["source_chain"][0]["source"] == "tencent_smartbox"


def test_tencent_realtime_quote_parser():
    session = FakeSession()
    session.queue(
        FakeResponse(
            content=(
                'v_sh600519="1~贵州茅台~600519~1458.49~1419.00~1413.10~55455~29757~25699~'
                '1458.48~3~1458.47~7~1458.46~36~1458.45~8~1458.44~360~1458.49~81~'
                '1458.50~42~1458.51~18~1458.52~8~1458.53~3~~20260424161425~39.49~'
                '2.78~1458.88~1413.10~1458.49/55455/8003410999~55455~800341~0.44~22.08~~~~3.23~18264.24~18264.24~6.74~~~1.26~";'
            ).encode("gb18030")
        )
    )
    client = make_client(session)

    result = client.quote_realtime(entity_from_symbol("600519", "600519.SH"))

    data = result["data"]
    assert data["symbol"] == "600519.SH"
    assert data["name"] == "贵州茅台"
    assert data["latest"] == 1458.49
    assert data["change_ratio"] == 2.78


def test_tencent_history_parser():
    session = FakeSession()
    session.queue(
        FakeResponse(
            json_payload={
                "code": 0,
                "data": {
                    "sh600519": {
                        "qfqday": [
                            ["2026-04-23", "1408.000", "1419.000", "1419.700", "1405.100", "37701.000"],
                            ["2026-04-24", "1413.100", "1458.490", "1458.880", "1413.100", "55455.000"],
                        ]
                    }
                },
            }
        )
    )
    client = make_client(session)

    result = client.quote_history(entity_from_symbol("600519", "600519.SH"), days=2, period="daily", adjust="qfq")

    candles = result["data"]["candles"]
    assert candles[0]["date"] == "2026-04-23"
    assert candles[1]["close"] == 1458.49


def test_eastmoney_rank_parser():
    session = FakeSession()
    session.queue(
        FakeResponse(
            json_payload={
                "rc": 0,
                "data": {
                    "total": 1,
                    "diff": [
                        {
                            "f12": "300422",
                            "f14": "博世科",
                            "f2": 5.56,
                            "f3": 20.086,
                            "f5": 38700561,
                            "f6": 213182897,
                            "f8": 7.48,
                        }
                    ],
                },
            }
        )
    )
    client = make_client(session)

    result = client.rank("gainers", 1)

    assert result["data"]["items"][0]["symbol"] == "300422.SZ"
    assert result["data"]["items"][0]["name"] == "博世科"


def test_cninfo_announcement_parser():
    session = FakeSession()
    session.queue(
        FakeResponse(
            json_payload={
                "announcements": [
                    {
                        "announcementTitle": "<em>贵州茅台</em>年报",
                        "secCode": "600519",
                        "secName": "贵州茅台",
                        "announcementTime": 1777000000000,
                        "announcementId": "demo",
                        "adjunctUrl": "finalpage/demo.PDF",
                    }
                ]
            }
        )
    )
    client = make_client(session)

    result = client.announcement(entity_from_symbol("600519", "600519.SH"), "年报", 10)

    item = result["data"]["items"][0]
    assert item["title"] == "贵州茅台年报"
    assert item["pdf_url"].startswith("https://static.cninfo.com.cn/")


def test_money_flow_falls_back_to_ths_for_industry(monkeypatch):
    client = SourceClient()

    def fail_akshare(scope, period, entity, limit):
        raise RuntimeError("eastmoney closed connection")

    def fake_ths(scope, period, limit):
        assert scope == "industry"
        assert period == "10d"
        assert limit == 3
        return {"scope": scope, "period": period, "items": [{"行业": "半导体"}]}

    monkeypatch.setattr(client, "_money_flow_akshare", fail_akshare)
    monkeypatch.setattr(client, "_money_flow_ths", fake_ths)

    result = client.money_flow("industry", "10d", None, 3)

    assert result["data"]["items"][0]["行业"] == "半导体"
    assert result["source_chain"][0]["source"] == "akshare_moneyflow"
    assert result["source_chain"][0]["ok"] is False
    assert result["source_chain"][1]["source"] == "akshare_ths_moneyflow"
    assert result["source_chain"][1]["ok"] is True


def test_extract_board_name_removes_question_words():
    assert _extract_board_name("半导体概念包含哪些股票") == "半导体"
    assert _extract_board_name("白 酒 板 块 有哪些股票") == "白酒"


def test_quiet_call_suppresses_third_party_output(capsys):
    def noisy_function():
        print("library stdout noise")
        print("library stderr noise", file=sys.stderr)
        return 42

    assert _quiet_call(noisy_function) == 42
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
