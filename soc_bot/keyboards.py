from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from config import SEVERITY_EMOJI, STATUS_EMOJI


def main_menu(is_admin=False):
    b = InlineKeyboardBuilder()
    b.button(text="📋 Incidents", callback_data="menu:incidents")
    b.button(text="🔎 Run Detection Scan", callback_data="menu:scan")
    b.button(text="📊 Reports & Stats", callback_data="menu:reports")
    b.button(text="👤 My Profile", callback_data="menu:profile")
    if is_admin:
        b.button(text="⚙️ Admin Panel", callback_data="menu:admin")
    b.adjust(1)
    return b.as_markup()


def back_button(target="menu:main"):
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Back", callback_data=target)
    return b.as_markup()


def incidents_menu():
    b = InlineKeyboardBuilder()
    b.button(text="➕ New Incident", callback_data="incident:new")
    b.button(text="📂 View All", callback_data="incident:list:all")
    b.button(text=f"{STATUS_EMOJI['new']} New", callback_data="incident:list:new")
    b.button(text=f"{STATUS_EMOJI['investigating']} Investigating", callback_data="incident:list:investigating")
    b.button(text=f"{STATUS_EMOJI['resolved']} Resolved", callback_data="incident:list:resolved")
    b.button(text="⬅️ Back", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def severity_picker(prefix="newinc"):
    b = InlineKeyboardBuilder()
    for sev, emoji in SEVERITY_EMOJI.items():
        b.button(text=f"{emoji} {sev.capitalize()}", callback_data=f"{prefix}:sev:{sev}")
    b.adjust(2)
    return b.as_markup()


def category_picker(prefix="newinc"):
    cats = ["authentication", "network", "web", "endpoint", "malware", "other"]
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=c.capitalize(), callback_data=f"{prefix}:cat:{c}")
    b.adjust(2)
    return b.as_markup()


def incident_list_kb(incidents, back_target="menu:incidents"):
    b = InlineKeyboardBuilder()
    for inc in incidents:
        emoji = STATUS_EMOJI.get(inc["status"], "")
        sev = SEVERITY_EMOJI.get(inc["severity"], "")
        b.button(
            text=f"{emoji}{sev} #{inc['id']} {inc['title'][:30]}",
            callback_data=f"incident:view:{inc['id']}",
        )
    b.button(text="⬅️ Back", callback_data=back_target)
    b.adjust(1)
    return b.as_markup()


def incident_detail_kb(incident_id, is_admin=False, is_analyst=False):
    b = InlineKeyboardBuilder()
    if is_analyst or is_admin:
        b.button(text="🔎 Investigate (Start)", callback_data=f"incident:investigate:{incident_id}")
        b.button(text="📝 Add Note", callback_data=f"incident:note:{incident_id}")
        b.button(text="✅ Mark Resolved", callback_data=f"incident:resolve:{incident_id}")
        b.button(text="🙋 Assign to Me", callback_data=f"incident:assign_me:{incident_id}")
        b.button(text="📄 Generate Report", callback_data=f"incident:report:{incident_id}")
    if is_admin:
        b.button(text="🗑 Delete Incident", callback_data=f"incident:delete:{incident_id}")
    b.button(text="⬅️ Back to list", callback_data="incident:list:all")
    b.adjust(1)
    return b.as_markup()


def confirm_delete_kb(incident_id):
    b = InlineKeyboardBuilder()
    b.button(text="⚠️ Yes, delete", callback_data=f"incident:delete_confirm:{incident_id}")
    b.button(text="Cancel", callback_data=f"incident:view:{incident_id}")
    b.adjust(2)
    return b.as_markup()


def admin_panel_kb():
    b = InlineKeyboardBuilder()
    b.button(text="👥 Pending Approvals", callback_data="admin:pending")
    b.button(text="🎭 Manage Roles", callback_data="admin:roles")
    b.button(text="📜 Audit Log", callback_data="admin:audit")
    b.button(text="⬅️ Back", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def pending_users_kb(users):
    b = InlineKeyboardBuilder()
    for u in users:
        name = u["username"] or u["full_name"] or str(u["telegram_id"])
        b.button(text=f"✅ Approve @{name}", callback_data=f"admin:approve:{u['id']}")
    b.button(text="⬅️ Back", callback_data="menu:admin")
    b.adjust(1)
    return b.as_markup()


def role_picker(user_id):
    b = InlineKeyboardBuilder()
    for role in ["viewer", "analyst", "admin"]:
        b.button(text=role.capitalize(), callback_data=f"admin:setrole:{user_id}:{role}")
    b.button(text="⬅️ Back", callback_data="admin:roles")
    b.adjust(1)
    return b.as_markup()


def users_list_kb(users, action="setrole_pick"):
    b = InlineKeyboardBuilder()
    for u in users:
        name = u["username"] or u["full_name"] or str(u["telegram_id"])
        b.button(text=f"@{name} ({u['role']})", callback_data=f"admin:{action}:{u['id']}")
    b.button(text="⬅️ Back", callback_data="menu:admin")
    b.adjust(1)
    return b.as_markup()


def scan_results_kb(findings_exist):
    b = InlineKeyboardBuilder()
    if findings_exist:
        b.button(text="➕ Create Incident From Findings", callback_data="scan:create_incident")
    b.button(text="⬅️ Back to Menu", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def reports_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📤 Export CSV", callback_data="export:csv")
    b.button(text="📤 Export PDF", callback_data="export:pdf")
    b.button(text="⬅️ Back", callback_data="menu:main")
    b.adjust(2, 1)
    return b.as_markup()


def cancel_kb():
    b = InlineKeyboardBuilder()
    b.button(text="❌ Cancel", callback_data="menu:main")
    return b.as_markup()
