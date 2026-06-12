"""Translation strings for the bot.

Two locales: `en` (English) and `id` (Bahasa Indonesia).
Lookup: STRINGS[locale][key].format(**kwargs).

All commands use a `/` prefix for unambiguous group-chat behaviour.
"""
from __future__ import annotations

from typing import Dict

DEFAULT_LOCALE = "en"
SUPPORTED = {"en", "id"}


STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "not_registered": (
            "Hi! This WhatsApp number isn't registered as a Trooper.\n"
            "Please ask Jonathan to add it."
        ),
        "help_menu": (
            "*Trooper Bot - Commands*\n"
            "(All commands start with `/`)\n\n"
            "- `/help` - show this menu\n"
            "- `/tasks` - your pending tasks (with names)\n"
            "- `/tasks all` - pending + last 5 done\n"
            "- `/info <Task ID>` - full task details + link\n"
            "- `/done <Task ID>` - mark task as Done\n"
            "  (bot will ask for a screenshot proof)\n"
            "- `/skip` - mark Done without proof\n"
            "- `/redo <Task ID>` - reopen a task\n"
            "- `/create <Task ID> | <Content> | <Link>` - create a new Main Task\n"
            "  (creates trackers for everyone automatically)\n"
            "- `/lang en` or `/lang id` - change language\n\n"
            "Tip: use `/lang id` to switch to Bahasa Indonesia."
        ),
        "lang_set": "Language set to *English*. Send `/help` to see commands.",
        "lang_usage": (
            "Usage: `/lang en` (English) or `/lang id` (Bahasa Indonesia)"
        ),
        "no_pending": "{name}, you're all clear - no pending tasks.",
        "pending_header": "*Pending tasks for {name}* ({count})",
        "pending_row": "{idx}. *{task_id}* - {name}\n   Status: {status}",
        "pending_footer": "Reply `/done <Task ID>` when finished, or `/info <Task ID>` for details.",
        "done_header": "Recently done (top 5):",
        "done_row": "  - {task_id} - {name} ({date})",
        "done_none": "  - none",
        "info_not_found": "Task `{task_id}` doesn't exist in the Main Task DB.",
        "info_block": (
            "*Task {task_id}*\n"
            "Name: {name}\n"
            "Created: {created}\n"
            "Complete: {complete}\n"
            "Link: {link}\n"
            "Your status: {status}"
        ),
        "info_no_tracker": "(no tracker row for you yet)",
        "missing_task_id": "Please include a Task ID, e.g. `/done T-001`",
        "task_not_found_for_user": (
            "I can't find Task `{task_id}` assigned to you.\n"
            "Send `/tasks` to see your list."
        ),
        "marked_done": "Got it. *{task_id}* set to *Done*.",
        "marked_redo": "Reopened. *{task_id}* set to *Not started*.",
        "send_proof": (
            "Please send a *screenshot* as proof for task *{task_id}*.\n\n"
            "Or send `/skip` to mark Done without proof."
        ),
        "proof_accepted": "Screenshot received. *{task_id}* marked as *Done* with proof attached.",
        "proof_download_failed": "Could not download your image. Please try again for task *{task_id}*.",
        "proof_upload_failed": "Failed to upload proof to Notion for *{task_id}*. Please try again.",
        "done_skipped": "*{task_id}* marked as *Done* (without proof).",
        "nothing_to_skip": "No pending task to skip. Use `/done <Task ID>` first.",
        "create_usage": (
            "Usage: `/create <Task ID> | <Content Name> | <Link>`\n"
            "Example: `/create 0042 | Why is faith important? | https://...`\n"
            "(Link is optional)"
        ),
        "create_dup": "Task ID `{task_id}` already exists. Use a different ID.",
        "created_main": (
            "Main Task *{task_id}* created.\n"
            "Content: {name}\n"
            "Tracker rows added for: {troopers}"
        ),
        "unknown": (
            "Unknown command, {name}. Send `/help` for the menu."
        ),
    },
    "id": {
        "not_registered": (
            "Hai! Nomor WhatsApp ini belum terdaftar sebagai Trooper.\n"
            "Mohon hubungi Jonathan untuk mendaftarkan."
        ),
        "help_menu": (
            "*Trooper Bot - Daftar Perintah*\n"
            "(Semua perintah diawali `/`)\n\n"
            "- `/help` - tampilkan menu ini\n"
            "- `/tasks` - tugas kamu yang belum selesai (dengan nama)\n"
            "- `/tasks all` - belum selesai + 5 terakhir yang selesai\n"
            "- `/info <Task ID>` - detail lengkap tugas + link\n"
            "- `/done <Task ID>` - tandai tugas sebagai Selesai\n"
            "  (bot akan minta screenshot sebagai bukti)\n"
            "- `/skip` - tandai Selesai tanpa bukti\n"
            "- `/redo <Task ID>` - buka kembali tugas\n"
            "- `/create <Task ID> | <Konten> | <Link>` - buat Main Task baru\n"
            "  (otomatis bikin tracker untuk semua orang)\n"
            "- `/lang en` atau `/lang id` - ganti bahasa\n\n"
            "Tip: pakai `/lang en` untuk bahasa Inggris."
        ),
        "lang_set": "Bahasa diatur ke *Bahasa Indonesia*. Kirim `/help` untuk lihat perintah.",
        "lang_usage": (
            "Cara pakai: `/lang en` (English) atau `/lang id` (Bahasa Indonesia)"
        ),
        "no_pending": "{name}, semua tugas sudah selesai - tidak ada yang tertunda.",
        "pending_header": "*Tugas tertunda {name}* ({count})",
        "pending_row": "{idx}. *{task_id}* - {name}\n   Status: {status}",
        "pending_footer": "Balas `/done <Task ID>` saat selesai, atau `/info <Task ID>` untuk detail.",
        "done_header": "Terakhir diselesaikan (5 teratas):",
        "done_row": "  - {task_id} - {name} ({date})",
        "done_none": "  - tidak ada",
        "info_not_found": "Task `{task_id}` tidak ditemukan di database Main Task.",
        "info_block": (
            "*Task {task_id}*\n"
            "Nama: {name}\n"
            "Dibuat: {created}\n"
            "Selesai: {complete}\n"
            "Link: {link}\n"
            "Status kamu: {status}"
        ),
        "info_no_tracker": "(belum ada tracker untuk kamu)",
        "missing_task_id": "Mohon sertakan Task ID, contoh: `/done T-001`",
        "task_not_found_for_user": (
            "Tidak menemukan Task `{task_id}` yang ditugaskan ke kamu.\n"
            "Kirim `/tasks` untuk melihat daftar."
        ),
        "marked_done": "Tercatat. *{task_id}* diatur sebagai *Selesai*.",
        "marked_redo": "Dibuka kembali. *{task_id}* diatur sebagai *Belum mulai*.",
        "send_proof": (
            "Kirim *screenshot* sebagai bukti untuk task *{task_id}*.\n\n"
            "Atau kirim `/skip` untuk tandai Selesai tanpa bukti."
        ),
        "proof_accepted": "Screenshot diterima. *{task_id}* ditandai *Selesai* dengan bukti terlampir.",
        "proof_download_failed": "Tidak bisa mengunduh gambar. Coba lagi untuk task *{task_id}*.",
        "proof_upload_failed": "Gagal mengunggah bukti ke Notion untuk *{task_id}*. Coba lagi.",
        "done_skipped": "*{task_id}* ditandai *Selesai* (tanpa bukti).",
        "nothing_to_skip": "Tidak ada task yang menunggu. Gunakan `/done <Task ID>` dulu.",
        "create_usage": (
            "Cara pakai: `/create <Task ID> | <Nama Konten> | <Link>`\n"
            "Contoh: `/create 0042 | Kenapa iman penting? | https://...`\n"
            "(Link opsional)"
        ),
        "create_dup": "Task ID `{task_id}` sudah ada. Pakai ID lain.",
        "created_main": (
            "Main Task *{task_id}* berhasil dibuat.\n"
            "Konten: {name}\n"
            "Tracker dibuat untuk: {troopers}"
        ),
        "unknown": (
            "Perintah tidak dikenal, {name}. Kirim `/help` untuk melihat menu."
        ),
    },
}


def t(locale: str | None, key: str, **kwargs) -> str:
    loc = locale if locale in SUPPORTED else DEFAULT_LOCALE
    template = STRINGS.get(loc, STRINGS[DEFAULT_LOCALE]).get(key)
    if template is None:
        template = STRINGS[DEFAULT_LOCALE].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
