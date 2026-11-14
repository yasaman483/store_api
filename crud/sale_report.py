from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.people import Person
from schemas.sale_report import GetReportType
from schemas.audit import AuditContext, AuditStatus
from schemas.people import Roles
from crud.audit_log import create_audit_log
from schemas.sale_report import ReportType
from schemas.payment_history import PaymentStatus
from schemas.orders import OrderStatus
from models.sale_report import SaleReport
from datetime import datetime, timedelta
from models.orders import Order
from models.payment_history import PaymentHistory
import logging

logger = logging.getLogger(__name__)


async def get_report(report: GetReportType, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="sale_report",
            event="GET_SALE_REPORT",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )

        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for creating discount')

    try:
        if report.report_type == ReportType.Daily:
            result = await db.execute(select(SaleReport).where(SaleReport.report_type == ReportType.Daily,
                                                               SaleReport.report_start >= report.start_date,
                                                               SaleReport.report_end <= report.end_date))
            reports = result.scalars()

        elif report.report_type == ReportType.Weekly:
            result = await db.execute(select(SaleReport).where(SaleReport.report_type == ReportType.Weekly,
                                                               SaleReport.report_start >= report.start_date,
                                                               SaleReport.report_end <= report.end_date))
            reports = result.scalars()

        elif report.report_type == ReportType.Monthly:
            result = await db.execute(select(SaleReport).where(SaleReport.report_type == ReportType.Monthly,
                                                               SaleReport.report_start >= report.start_date,
                                                               SaleReport.report_end <= report.end_date))
            reports = result.scalars()

        elif report.report_type == ReportType.Yearly:
            result = await db.execute(select(SaleReport).where(SaleReport.report_type == ReportType.Yearly,
                                                               SaleReport.report_start >= report.start_date,
                                                               SaleReport.report_end <= report.end_date))
            reports = result.scalars()

        if not reports:
            raise HTTPException(status_code=404, detail="Report not found")

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="sale_report",
            event="GET_SALE_REPORT",
            old_value=None,
            new_value=None
        )

        await db.commit()

        return reports

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.error(f"Get sale report failed")
        await db.rollback()
        raise


async def daily_scheduler(db: AsyncSession):
    result = await db.execute(select(Order).where(Order.order_date == datetime.today()-timedelta(days=1),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    orders = result.scalars()

    total_amount_day = 0
    products = {}
    hours = {k: 0 for k in range(0, 25)}
    for order in orders:
        total_amount_day += order.total_amount_discounted
        hours[order.order_date.hour] += 1
        for order_item in order.oreder_items:
            if order_item.product_id not in products.keys():
                products[order_item.product_id] = 1
            else:
                products[order_item.product_id] += 1

    products = dict(sorted(products.items(), key=lambda item: item[1]))

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_date == datetime.today()-timedelta(days=1),
                                                           PaymentHistory.payment_status == PaymentStatus.FAILED))
    payments = result.scalars()

    metrics = {
        "total_amount": total_amount_day,
        "total_orders": len(orders),
        "five_popular_items_id": products.keys()[:5],
        "sale_in_different_hours": hours,
        "number_of_failed_payments": len(payments)
    }

    result = await db.execute(select(Order).where(Order.order_date == datetime.today()-timedelta(days=2),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    last_day_orders = result.scalars()

    result = await db.execute(select(Order).where(Order.order_date == datetime.today()-timedelta(weeks=1, days=1),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    last_week_orders = result.scalars()

    total_amount_last_day = sum(
        [order.total_amount_discounted for order in last_day_orders])
    total_amount_last_week = sum(
        [order.total_amount_discounted for order in last_week_orders])

    comparison = {
        "total_amount_last_day": total_amount_last_day,
        "total_amount_today": total_amount_day,
        "increament_rate_compare_to_last_day": (total_amount_day - total_amount_last_day)*100,
        "total_amount_in_similar_day_last_week": total_amount_last_week,
        "increament_rate_compare_to_last_week": (total_amount_day - total_amount_last_week)*100
    }

    new_report = SaleReport(
        reoprt_type=ReportType.Daily,
        report_start=datetime.today()-timedelta(days=1),
        report_end=datetime.today()-timedelta(days=1),
        metrics=metrics,
        comparison=comparison,
        generated_at=datetime.now()
    )

    db.add(new_report)
    await db.commit()

    return new_report


async def weekly_scheduler(db: AsyncSession):
    result = await db.execute(select(Order).where(Order.order_date >= datetime.today()-timedelta(weeks=1),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    orders = result.scalars()

    total_amount_week = 0
    products = {}
    days = {d: 0 for d in range(1, 8)}
    for order in orders:
        total_amount_week += order.total_amount_discounted
        days[order.order_date.day] += 1
        for order_item in order.oreder_items:
            if order_item.product_id not in products.keys():
                products[order_item.product_id] = 1
            else:
                products[order_item.product_id] += 1

    products = dict(sorted(products.items(), key=lambda item: item[1]))

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_date >= datetime.today()-timedelta(weeks=1),
                                                           PaymentHistory.payment_date < datetime.today(),
                                                           PaymentHistory.payment_status == PaymentStatus.FAILED))
    payments = result.scalars()

    metrics = {
        "total_amount": total_amount_week,
        "total_orders": len(orders),
        "five_popular_items_id_per_days": products.keys()[:5],
        "sale_in_different_days": days,
        "number_of_failed_payments": len(payments)
    }

    result = await db.execute(select(Order).where(Order.order_date == datetime.today()-timedelta(weeks=1),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    last_week_orders = result.scalars()

    total_amount_last_week = sum(
        [order.total_amount_discounted for order in last_week_orders])

    comparison = {
        "total_amount_last_week": total_amount_last_week,
        "total_amount_current_week": total_amount_week,
        "increament_rate_compare_to_last_week": (total_amount_week - total_amount_last_week)*100
    }

    new_report = SaleReport(
        reoprt_type=ReportType.Weekly,
        report_start=datetime.today()-timedelta(weeks=1),
        report_end=datetime.today()-timedelta(days=1),
        metrics=metrics,
        comparison=comparison,
        generated_at=datetime.now()
    )

    db.add(new_report)
    await db.commit()

    return new_report


async def monthly_scheduler(db: AsyncSession):
    month = datetime.today().month
    if month == 1:
        month = 12
        year = datetime.today().year
    else:
        month -= 1
        year = datetime.today().year

    result = await db.execute(select(Order).where(Order.order_date >= datetime(year=datetime.today().year, month=month, day=1, hour=0, minute=0, second=0),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    orders = result.scalars()

    last_day = 0
    total_amount_month = 0
    products = {}
    weeks = {w: 0 for w in range(0, 7)}
    for order in orders:
        total_amount_month += order.total_amount_discounted
        weeks[order.order_date.weekday] += 1
        if order.order_date.day > last_day:
            last_day = order.order_date.day

        for order_item in order.oreder_items:
            if order_item.product_id not in products.keys():
                products[order_item.product_id] = 1
            else:
                products[order_item.product_id] += 1

    products = dict(sorted(products.items(), key=lambda item: item[1]))

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_date >= datetime(year=datetime.today().year, month=month, day=1, hour=0, minute=0, second=0),
                                                           PaymentHistory.payment_date < datetime.today(),
                                                           PaymentHistory.payment_status == PaymentStatus.FAILED))
    payments = result.scalars()

    metrics = {
        "total_amount": total_amount_month,
        "total_orders": len(orders),
        "five_popular_items_id_per_days": products.keys()[:5],
        "sale_in_different_days": weeks,
        "number_of_failed_payments": len(payments)
    }

    result = await db.execute(select(Order).where(Order.order_date >= datetime(year=datetime.today().year, month=month, day=1, hour=0, minute=0, second=0),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    last_month_orders = result.scalars()

    total_amount_last_month = sum(
        [order.total_amount_discounted for order in last_month_orders])

    comparison = {
        "total_amount_last_month": total_amount_last_month,
        "total_amount_current_month": total_amount_month,
        "increament_rate_compare_to_last_month": (total_amount_month - total_amount_last_month)*100
    }

    new_report = SaleReport(
        reoprt_type=ReportType.Monthly,
        report_start=datetime(year=year, month=month,
                              day=1, hour=0, minute=0, second=0),
        report_end=datetime(year=year, month=month, day=1,
                            hour=24, minute=59, second=59),
        metrics=metrics,
        comparison=comparison,
        generated_at=datetime.now()
    )

    db.add(new_report)
    await db.commit()

    return new_report


async def yearly_scheduler(db: AsyncSession):
    year = datetime.today().year-1
    result = await db.execute(select(Order).where(Order.order_date >= datetime(year=year, month=1, day=1, hour=0, minute=0, second=0),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    orders = result.scalars()

    total_amount_year = 0
    products = {}
    months = {m: 0 for m in range(1, 13)}
    for order in orders:
        total_amount_year += order.total_amount_discounted
        months[order.order_date.month] += 1
        for order_item in order.oreder_items:
            if order_item.product_id not in products.keys():
                products[order_item.product_id] = 1
            else:
                products[order_item.product_id] += 1

    products = dict(sorted(products.items(), key=lambda item: item[1]))

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_date >= datetime(year=year, month=1, day=1, hour=0, minute=0, second=0),
                                                           PaymentHistory.payment_date < datetime.today(),
                                                           PaymentHistory.payment_status == PaymentStatus.FAILED))
    payments = result.scalars()

    metrics = {
        "total_amount": total_amount_year,
        "total_orders": len(orders),
        "five_popular_items_id_per_days": products.keys()[:5],
        "sale_in_different_days": months,
        "number_of_failed_payments": len(payments)
    }

    result = await db.execute(select(Order).where(Order.order_date >= datetime(year=year, month=1, day=1, hour=0, minute=0, second=0),
                                                  Order.order_date < datetime.today(),
                                                  Order.order_status == OrderStatus.CONFIRMED))
    last_year_orders = result.scalars()

    total_amount_last_year = sum(
        [order.total_amount_discounted for order in last_year_orders])

    comparison = {
        "total_amount_last_week": total_amount_last_year,
        "total_amount_current_week": total_amount_year,
        "increament_rate_compare_to_last_week": (total_amount_year - total_amount_last_year)*100
    }

    new_report = SaleReport(
        reoprt_type=ReportType.Yearly,
        report_start=datetime(year=year, month=1, day=1,
                              hour=0, minute=0, second=0),
        report_end=datetime(year=year, month=12, day=31,
                            hour=24, minute=59, second=59),
        metrics=metrics,
        comparison=comparison,
        generated_at=datetime.now()
    )

    db.add(new_report)
    await db.commit()

    return new_report
