from aiogram import Router
from . import start, incidents, scan, admin, reports, export

main_router = Router()
main_router.include_router(start.router)
main_router.include_router(incidents.router)
main_router.include_router(scan.router)
main_router.include_router(admin.router)
main_router.include_router(reports.router)
main_router.include_router(export.router)
