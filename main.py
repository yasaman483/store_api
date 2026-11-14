from fastapi import FastAPI, Depends
from database import connect
import logging
from datetime import datetime, UTC
from contextlib import asynccontextmanager
from routers import discount_granted, people, categories, products, discount, wallet, orders, order_items, payment_history, caret, caret_items, sale_report
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from crud.sale_report import daily_scheduler, weekly_scheduler, monthly_scheduler, yearly_scheduler
from database.connect import get_db


logging.basicConfig(
    filename='./logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with connect.engine.begin() as conn:
            await conn.run_sync(connect.Base.metadata.create_all)

        info = {
            "event": "Connection done successfully",
            "start_time": datetime.now(UTC)
        }
        logging.info(info)

        scheduler = AsyncIOScheduler()

        db = get_db()
        scheduler.add_job(
            daily_scheduler,
            args=[db],
            trigger="cron",
            hour=0,
            minute=5,
            id="daily_report",
            timezone="UTC"
        )

        db = get_db()
        scheduler.add_job(
            weekly_scheduler,
            args=[db],
            trigger="cron",
            day_of_week="mon",
            hour=0,
            minute=5,
            id="weekly_report",
            timezone="UTC"
        )

        db = get_db()
        scheduler.add_job(
            monthly_scheduler,
            args=[db],
            trigger="cron",
            day=1,
            hour=0,
            minute=5,
            id="monthly_report",
            timezone="UTC"
        )

        db = get_db()
        scheduler.add_job(
            yearly_scheduler,
            args=[db],
            trigger="cron",
            month=1,
            day=1,
            hour=0,
            minute=5,
            id="yearly_report",
            timezone="UTC"
        )

    except Exception:
        error = {
            "event": f'Connection could not be made',
            "time": datetime.now(UTC)
        }
        logging.error(error)
        raise

    yield

    info = {
        "event": "The database shutdown successfully",
        "end_time": datetime.now(UTC)
    }
    logging.info(info)
    await connect.engine.dispose()


app = FastAPI(lifespan=lifespan)


app.include_router(wallet.router)
app.include_router(people.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(caret.router)
app.include_router(caret_items.router)
app.include_router(orders.router)
app.include_router(order_items.router)
app.include_router(discount.router)
app.include_router(discount_granted.router)
app.include_router(payment_history.router)
app.include_router(sale_report.router)
