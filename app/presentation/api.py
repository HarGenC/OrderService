from http import HTTPStatus
from uuid import UUID
from venv import logger
from dependency_injector.wiring import Provide, inject

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.application.container import ApplicationContainer
from app.application.create_order import CreateOrderUseCase, OrderDTO
from app.application.exceptions import (
    InsufficientQuantity,
    OrderNotFound,
    PaymentNotFound,
)
from app.application.get_order import GetOrderUseCase
from app.application.process_callback import CallbackProcessingUseCase
from app.core.models import Order, RequestCallback

router = APIRouter(prefix="/api")


class OrderCreateRequest(OrderDTO):  # Наследуется от DTO
    pass


class OrderResponseModel(Order):  # Наследуется от DTO
    pass


@router.post(
    "/orders",
    status_code=HTTPStatus.CREATED,
    response_model=OrderResponseModel,
)
@inject
async def create_order(
    order: OrderCreateRequest,
    create_order_use_case: CreateOrderUseCase = Depends(
        Provide[ApplicationContainer.create_order_use_case]
    ),
):
    try:
        return await create_order_use_case(order)
    except InsufficientQuantity:
        return JSONResponse(
            content={"message": "Insufficient product"},
            status_code=HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        logger.error(e)
        return JSONResponse(
            content={"message": "Internal server error while creating order"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@router.get("/orders/{order_id}", status_code=200, response_model=OrderResponseModel)
@inject
async def get_order(
    order_id: UUID,
    get_order_use_case: GetOrderUseCase = Depends(
        Provide[ApplicationContainer.get_order_use_case]
    ),
):
    try:
        return await get_order_use_case(order_id)
    except OrderNotFound:
        return JSONResponse(
            content={"message": "Order not found"},
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            content={"message": "Internal server error while getting order"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@router.post("/orders/payment-callback", status_code=200)
@inject
async def payment_callback_processing(
    request_callback: RequestCallback,
    callback_processing_use_case: CallbackProcessingUseCase = Depends(
        Provide[ApplicationContainer.callback_processing_use_case]
    ),
):
    try:
        await callback_processing_use_case(request_callback)
        return
    except PaymentNotFound:
        return JSONResponse(
            content={"message": "Payment not found"},
            status_code=HTTPStatus.NOT_FOUND,
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            content={"message": "Internal server error while callback processing"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
