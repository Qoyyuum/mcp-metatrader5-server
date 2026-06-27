"""Unit tests for trading tools."""

import importlib
from types import SimpleNamespace

import pytest

mt5_main = importlib.import_module("mcp_mt5.main")


class Mt5NamedTuple:
    """Small stand-in for MT5 namedtuple responses."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def _asdict(self):
        return dict(self.__dict__)


def make_position(**overrides):
    data = {
        "ticket": 123456789,
        "time": 1609459200,
        "time_msc": 1609459200000,
        "time_update": 1609459200,
        "time_update_msc": 1609459200000,
        "type": 0,
        "magic": 12345,
        "identifier": 123456789,
        "reason": 0,
        "volume": 0.1,
        "price_open": 1.10000,
        "sl": 0.0,
        "tp": 0.0,
        "price_current": 1.10050,
        "swap": 0.0,
        "profit": 5.0,
        "symbol": "EURUSD",
        "comment": "Test position",
        "external_id": "",
    }
    data.update(overrides)
    return Mt5NamedTuple(**data)


def make_order_result(request):
    return Mt5NamedTuple(
        retcode=10009,
        deal=987654321,
        order=123456790,
        volume=request["volume"],
        price=request["price"],
        bid=1.10000,
        ask=1.10002,
        comment="Done",
        request_id=1,
        retcode_external=0,
        request=request,
    )


@pytest.mark.unit
class TestClosePosition:
    """Test close_position request construction."""

    def test_close_buy_position_sends_sell_with_position_ticket(self, mock_mt5, monkeypatch):
        """Closing a buy position must include the target position ticket."""
        monkeypatch.setattr(mt5_main, "mt5", mock_mt5)
        mock_mt5.positions_get.return_value = [make_position(type=mock_mt5.ORDER_TYPE_BUY)]
        mock_mt5.symbol_info_tick.return_value = SimpleNamespace(bid=1.10000, ask=1.10002)
        mock_mt5.symbol_info.return_value = SimpleNamespace(filling_mode=2, trade_exemode=2)
        mock_mt5.order_send.side_effect = make_order_result

        result = mt5_main.close_position(
            ticket=123456789, deviation=20, magic=123, comment="Close test"
        )

        sent_request = mock_mt5.order_send.call_args.args[0]
        assert sent_request == {
            "action": mock_mt5.TRADE_ACTION_DEAL,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": mock_mt5.ORDER_TYPE_SELL,
            "price": 1.10000,
            "position": 123456789,
            "deviation": 20,
            "comment": "Close test",
            "magic": 123,
            "type_filling": mock_mt5.ORDER_FILLING_IOC,
        }
        assert result.request["position"] == 123456789

    def test_close_sell_position_sends_buy_at_ask(self, mock_mt5, monkeypatch):
        """Closing a sell position should use a buy order at current ask."""
        monkeypatch.setattr(mt5_main, "mt5", mock_mt5)
        mock_mt5.positions_get.return_value = [make_position(type=mock_mt5.ORDER_TYPE_SELL)]
        mock_mt5.symbol_info_tick.return_value = SimpleNamespace(bid=1.10000, ask=1.10002)
        mock_mt5.symbol_info.return_value = SimpleNamespace(filling_mode=2, trade_exemode=2)
        mock_mt5.order_send.side_effect = make_order_result

        mt5_main.close_position(ticket=123456789, type_filling=mock_mt5.ORDER_FILLING_FOK)

        sent_request = mock_mt5.order_send.call_args.args[0]
        assert sent_request["type"] == mock_mt5.ORDER_TYPE_BUY
        assert sent_request["price"] == 1.10002
        assert sent_request["position"] == 123456789
        assert sent_request["type_filling"] == mock_mt5.ORDER_FILLING_FOK

    def test_close_position_missing_ticket_fails_before_order_send(self, mock_mt5, monkeypatch):
        """Missing positions should fail without sending a new order."""
        monkeypatch.setattr(mt5_main, "mt5", mock_mt5)
        mock_mt5.positions_get.return_value = []

        with pytest.raises(ValueError, match="Position with ticket 123456789 was not found"):
            mt5_main.close_position(ticket=123456789)

        mock_mt5.order_send.assert_not_called()
