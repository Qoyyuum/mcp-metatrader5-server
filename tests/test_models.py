"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from mcp_mt5.main import (
    AccountInfo,
    Deal,
    OrderRequest,
    Position,
    SymbolInfo,
)


@pytest.mark.unit
class TestAccountInfoModel:
    """Test AccountInfo Pydantic model."""

    def test_valid_account_info(self):
        """Test creating valid AccountInfo."""
        data = {
            "login": 123456,
            "trade_mode": 0,
            "leverage": 100,
            "limit_orders": 200,
            "margin_so_mode": 0,
            "trade_allowed": True,
            "trade_expert": True,
            "margin_mode": 0,
            "currency_digits": 2,
            "fifo_close": False,
            "balance": 10000.0,
            "credit": 0.0,
            "profit": 150.50,
            "equity": 10150.50,
            "margin": 500.0,
            "margin_free": 9650.50,
            "margin_level": 2030.1,
            "margin_so_call": 50.0,
            "margin_so_so": 30.0,
            "margin_initial": 0.0,
            "margin_maintenance": 0.0,
            "assets": 0.0,
            "liabilities": 0.0,
            "commission_blocked": 0.0,
            "name": "Test Account",
            "server": "TestServer",
            "currency": "USD",
            "company": "Test Company",
        }

        account = AccountInfo(**data)

        assert account.login == 123456
        assert account.balance == 10000.0
        assert account.equity == 10150.50
        assert account.currency == "USD"

    def test_account_info_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        data = {
            "login": 123456,
            # Missing other required fields
        }

        with pytest.raises(ValidationError):
            AccountInfo(**data)


@pytest.mark.unit
class TestOrderRequestModel:
    """Test OrderRequest Pydantic model."""

    def test_valid_order_request(self):
        """Test creating valid OrderRequest."""
        data = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,  # ORDER_TYPE_BUY
            "price": 1.10000,
            "sl": 1.09500,
            "tp": 1.10500,
            "deviation": 20,
            "magic": 12345,
            "comment": "Test order",
        }

        order = OrderRequest(**data)

        assert order.symbol == "EURUSD"
        assert order.volume == 0.1
        assert order.price == 1.10000
        assert order.sl == 1.09500
        assert order.tp == 1.10500

    def test_order_request_optional_fields(self):
        """Test OrderRequest with only required fields."""
        data = {
            "action": 1,
            "symbol": "EURUSD",
            "volume": 0.1,
            "type": 0,
            "price": 1.10000,
        }

        order = OrderRequest(**data)

        assert order.sl is None
        assert order.tp is None
        assert order.deviation is None
        assert order.magic is None
        assert order.comment is None

    def test_close_position_order_preserves_position_ticket(self):
        """Test close-position deal payload keeps the target position ticket."""
        order = OrderRequest(
            action=1,
            symbol="EURUSD",
            volume=0.1,
            type=1,
            price=1.1,
            position=123456789,
            deviation=20,
        )

        assert order.position == 123456789
        assert order.model_dump(exclude_none=True)["position"] == 123456789

    def test_modify_pending_order_requires_order_and_price_only(self):
        """Test modify pending payload does not require create-only fields."""
        order = OrderRequest(
            action=7,
            order=34784473,
            symbol="NZDUSD",
            price=0.57464,
            sl=0.57877,
            tp=0.56638,
        )

        assert order.action == 7
        assert order.order == 34784473
        assert order.symbol == "NZDUSD"
        assert order.price == 0.57464
        assert order.volume is None
        assert order.type is None

    def test_delete_pending_order_requires_order_only(self):
        """Test delete pending payload accepts order without create-only fields."""
        order = OrderRequest(
            action=8,
            order=34784473,
            symbol="NZDUSD",
        )

        assert order.action == 8
        assert order.order == 34784473
        assert order.symbol == "NZDUSD"
        assert order.volume is None
        assert order.type is None
        assert order.price is None

    def test_modify_pending_order_missing_order_fails(self):
        """Test modify pending validation enforces order ticket."""
        with pytest.raises(ValueError, match="Pending order modify requires: order"):
            OrderRequest(
                action=7,
                symbol="NZDUSD",
                price=0.57464,
            )


@pytest.mark.unit
class TestSymbolInfoModel:
    """Test SymbolInfo Pydantic model."""

    def test_valid_symbol_info(self):
        """Test creating valid SymbolInfo."""
        data = {
            "name": "EURUSD",
            "description": "Euro vs US Dollar",
            "digits": 5,
            "spread": 2,
            "bid": 1.10000,
            "ask": 1.10002,
        }

        symbol = SymbolInfo(**data)

        assert symbol.name == "EURUSD"
        assert symbol.digits == 5
        assert symbol.bid == 1.10000

    def test_symbol_info_all_optional_fields(self):
        """Test SymbolInfo with all fields as None except name."""
        symbol = SymbolInfo(name="EURUSD")

        assert symbol.name == "EURUSD"
        assert symbol.description is None
        assert symbol.bid is None


@pytest.mark.unit
class TestPositionModel:
    """Test Position Pydantic model."""

    def test_valid_position(self):
        """Test creating valid Position."""
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
            "sl": 1.09500,
            "tp": 1.10500,
            "price_current": 1.10050,
            "swap": 0.0,
            "profit": 5.0,
            "symbol": "EURUSD",
            "comment": "Test position",
            "external_id": "",
        }

        position = Position(**data)

        assert position.ticket == 123456789
        assert position.symbol == "EURUSD"
        assert position.volume == 0.1
        assert position.profit == 5.0


@pytest.mark.unit
class TestDealModel:
    """Test Deal Pydantic model."""

    def test_valid_deal(self):
        """Test creating valid Deal."""
        data = {
            "ticket": 987654321,
            "order": 123456789,
            "time": 1609459200,
            "time_msc": 1609459200000,
            "type": 0,
            "entry": 0,
            "magic": 12345,
            "position_id": 123456789,
            "reason": 0,
            "volume": 0.1,
            "price": 1.10000,
            "commission": -0.50,
            "swap": 0.0,
            "profit": 5.0,
            "fee": 0.0,
            "symbol": "EURUSD",
            "comment": "Test deal",
            "external_id": "",
        }

        deal = Deal(**data)

        assert deal.ticket == 987654321
        assert deal.symbol == "EURUSD"
        assert deal.volume == 0.1
        assert deal.profit == 5.0
        assert deal.commission == -0.50
