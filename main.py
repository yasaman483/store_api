from fastapi import FastAPI
from database import connect
import logging
from contextlib import asynccontextmanager
from routers import discount_granted, employee_info, people, categories, products, discount, wallet, orders, order_items, payment_history
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

        info = {"event": "Connection done successfully"}
        logging.info(info)

    except Exception as ex:
        error = {"event": f'Connection could not be made', "error": f'{ex}'}
        logging.error(error)
        raise ex

    yield

    info = {"event": "The database shutdown successfully"}
    logging.info(info)
    await connect.engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(people.router)
app.include_router(employee_info.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(discount.router)
app.include_router(discount_granted.router)
app.include_router(wallet.router)
app.include_router(orders.router)
app.include_router(order_items.router)
app.include_router(payment_history.router)
