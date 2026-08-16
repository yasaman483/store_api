from fastapi import FastAPI
from database import connect
import logging
from contextlib import asynccontextmanager
from routers import people, report_to, categories, products, discount, discount_people, wallet, orders, order_items, payment_history
from seed import seed_manager

logging.basicConfig(filename='./logs.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with connect.engine.begin() as conn:
            await conn.run_sync(connect.Base.metadata.create_all)

        await seed_manager()

        logging.info('connection done successfully.')

    except Exception as ex:
        logging.error(f'connection could not be made due to the error: {ex}')
        raise ex

    yield

    await connect.engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(people.router)
app.include_router(report_to.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(discount.router)
app.include_router(discount_people.router)
app.include_router(wallet.router)
app.include_router(orders.router)
app.include_router(order_items.router)
app.include_router(payment_history.router)
