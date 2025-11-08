import jwt
import hashlib
import json
import math
import os
import uuid
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

ALLOWED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp'
}

MAX_AVATAR_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_COVER_FILE_SIZE = 5 * 1024 * 1024   # 5MB

MONTHLY_TICKET_UNIT = Decimal('200')

ADMIN_ROLE = 9

MESSAGE_TYPE_SUBSCRIPTION = 101
MESSAGE_TYPE_VOTE = 102
MESSAGE_TYPE_COMMENT_REPLY = 103

MESSAGE_TYPE_SIGN_CONTRACT = 201
MESSAGE_TYPE_AUDIT_RESULT = 202

MESSAGE_TYPE_WORK_UPDATE = 301

MESSAGE_TYPE_SYSTEM = 501

ADMIN_MESSAGE_TYPE_USER = MESSAGE_TYPE_SYSTEM
ADMIN_MESSAGE_TYPE_WORK = MESSAGE_TYPE_AUDIT_RESULT
ADMIN_MESSAGE_TYPE_COMMENT = MESSAGE_TYPE_AUDIT_RESULT
ADMIN_MESSAGE_TYPE_CHAPTER = MESSAGE_TYPE_AUDIT_RESULT

ADMIN_ACTION_TARGET_SYSTEM = 0
ADMIN_ACTION_TARGET_USER = 1
ADMIN_ACTION_TARGET_WORK = 2
ADMIN_ACTION_TARGET_COMMENT = 3
ADMIN_ACTION_TARGET_CHAPTER = 4

USER_ACTION_TARGET_UNKNOWN = 0
USER_ACTION_TARGET_WORK = 1
USER_ACTION_TARGET_CHAPTER = 2
USER_ACTION_TARGET_COMMENT = 3
USER_ACTION_TARGET_PROFILE = 4
USER_ACTION_TARGET_BOOKSHELF = 5
USER_ACTION_TARGET_SUBSCRIPTION = 6

USER_PERMISSION_FIELDS = {
    'can_publish': 'can_publish',
    'can_subscribe': 'can_subscribe',
    'can_recharge': 'can_recharge',
    'can_comment': 'can_comment',
    'can_vote': 'can_vote'
}

USER_PERMISSION_LABELS = {
    'can_publish': '发表作品',
    'can_subscribe': '订阅内容',
    'can_recharge': '充值点券',
    'can_comment': '发表评论',
    'can_vote': '参与投票'
}

FEEDBACK_EVENT_CLICK = 1
FEEDBACK_EVENT_VIEW = 2
FEEDBACK_EVENT_COLLECT = 3
FEEDBACK_EVENT_READ = 4
FEEDBACK_EVENT_SUBSCRIBE = 5
FEEDBACK_EVENT_VOTE = 6

FEEDBACK_EVENT_ALIASES = {
    'click': FEEDBACK_EVENT_CLICK,
    'view': FEEDBACK_EVENT_VIEW,
    'collect': FEEDBACK_EVENT_COLLECT,
    'read': FEEDBACK_EVENT_READ,
    'subscribe': FEEDBACK_EVENT_SUBSCRIBE,
    'vote': FEEDBACK_EVENT_VOTE,
}

FEEDBACK_EVENT_WEIGHTS = {
    FEEDBACK_EVENT_CLICK: 1.0,
    FEEDBACK_EVENT_VIEW: 1.2,
    FEEDBACK_EVENT_COLLECT: 3.0,
    FEEDBACK_EVENT_READ: 1.8,
    FEEDBACK_EVENT_SUBSCRIBE: 2.5,
    FEEDBACK_EVENT_VOTE: 2.8,
}

FEEDBACK_DEFAULT_WEIGHT = 1.0
FEEDBACK_MAX_WEIGHT_DELTA = 5.0
FEEDBACK_MIN_WEIGHT_DELTA = 0.05
FEEDBACK_MAX_AGG_WEIGHT = 60.0
FEEDBACK_RETENTION_DAYS = 180
FEEDBACK_DECAY_DAYS = 60

WORK_MODERATION_FIELDS = {
    'is_hidden': 'is_hidden',
    'chapters_blocked': 'chapters_blocked',
    'updates_blocked': 'updates_blocked',
    'subscriptions_blocked': 'subscriptions_blocked',
    'votes_blocked': 'votes_blocked',
    'note': 'note'
}

WORK_MODERATION_LABELS = {
    'is_hidden': '作品可见性',
    'chapters_blocked': '章节访问',
    'updates_blocked': '作品更新',
    'subscriptions_blocked': '订阅行为',
    'votes_blocked': '投票行为'
}

ADMIN_REGISTRATION_KEY = getattr(settings, 'ADMIN_REGISTRATION_KEY', 'wmtxym')

# 上传图片通用处理函数
def _save_uploaded_image(file_obj, subdir, max_size):
    content_type = file_obj.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError('不支持的图片类型，仅支持 JPG/PNG/GIF/WebP')

    if file_obj.size > max_size:
        max_size_mb = max_size // (1024 * 1024)
        raise ValueError(f'图片大小不能超过 {max_size_mb}MB')

    extension = os.path.splitext(file_obj.name)[1].lower()
    allowed_extensions = set(ALLOWED_IMAGE_TYPES.values())
    if extension not in allowed_extensions:
        extension = ALLOWED_IMAGE_TYPES.get(content_type, '.jpg')

    filename = f"{uuid.uuid4().hex}{extension}"
    upload_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(upload_dir, exist_ok=True)

    storage = FileSystemStorage(location=upload_dir, base_url=f"{settings.MEDIA_URL}{subdir}/")
    saved_name = storage.save(filename, file_obj)
    return storage.url(saved_name)

# 工具函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _get_client_ip(request):
    if not request:
        return ''
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def _serialize_extra(extra):
    if extra is None:
        return ''
    if isinstance(extra, (dict, list)):
        try:
            return json.dumps(extra, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps({'value': str(extra)}, ensure_ascii=False)
    if isinstance(extra, (str, bytes)):
        return extra if isinstance(extra, str) else extra.decode('utf-8', errors='ignore')
    try:
        return json.dumps(extra, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(extra)


def _safe_load_json(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return value


def _parse_time_param(value):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _fetch_user_profile(user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.user_id, u.username, u.phone, u.email,
                   u.create_time, u.last_login_time, u.role,
                   r.nickname, r.avatar_url, r.balance,
                   a.intro, a.pen_name
            FROM users u
            LEFT JOIN readers r ON u.user_id = r.reader_id
            LEFT JOIN authors a ON u.user_id = a.author_id
            WHERE u.user_id = %s
        """, [user_id])

        row = cursor.fetchone()

    if not row:
        return None

    balance_value = float(row[9]) if row[9] is not None else 0.0

    profile = {
        'user_id': row[0],
        'username': row[1],
        'phone': row[2],
        'email': row[3],
        'create_time': row[4].isoformat() if row[4] else None,
        'last_login_time': row[5].isoformat() if row[5] else None,
        'role': row[6],
        'nickname': row[7] or row[11] or row[1],
        'avatar_url': row[8] or '',
        'balance': balance_value,
        'intro': row[10] or ''
    }

    return profile


def _fetch_user_stats(user_id):
    stats = {
        'total_reading': 0,
        'reading_time': 0.0,
        'collections': 0,
        'votes': 0
    }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT ch.work_id) AS total_reading,
                   COALESCE(SUM(ch.word_count * (rr.progress / 100)), 0) AS total_words
            FROM reading_records rr
            JOIN chapters ch ON rr.chapter_id = ch.chapter_id
            WHERE rr.reader_id = %s
        """, [user_id])

        reading_row = cursor.fetchone()
        if reading_row:
            stats['total_reading'] = int(reading_row[0]) if reading_row[0] else 0
            total_words = float(reading_row[1]) if reading_row[1] else 0.0
            stats['reading_time'] = round(total_words / 18000, 2) if total_words else 0.0

        cursor.execute("SELECT COUNT(*) FROM collections WHERE reader_id = %s", [user_id])
        collections_row = cursor.fetchone()
        if collections_row and collections_row[0] is not None:
            stats['collections'] = int(collections_row[0])

        cursor.execute("SELECT COALESCE(SUM(count), 0) FROM votes WHERE reader_id = %s", [user_id])
        votes_row = cursor.fetchone()
        if votes_row and votes_row[0] is not None:
            stats['votes'] = int(votes_row[0])

    return stats


def _ensure_user_permission_record(cursor, user_id):
    cursor.execute("SELECT user_id FROM user_permissions WHERE user_id = %s", [user_id])
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO user_permissions (
                user_id, can_publish, can_subscribe, can_recharge, can_comment, can_vote,
                create_time, update_time
            )
            VALUES (%s, 1, 1, 1, 1, 1, NOW(), NOW())
            """,
            [user_id]
        )


def _ensure_user_permission_exists(user_id):
    with connection.cursor() as cursor:
        _ensure_user_permission_record(cursor, user_id)


def _get_user_permissions(user_id):
    with connection.cursor() as cursor:
        _ensure_user_permission_record(cursor, user_id)
        cursor.execute(
            """
            SELECT can_publish, can_subscribe, can_recharge, can_comment, can_vote
            FROM user_permissions WHERE user_id = %s
            """,
            [user_id]
        )
        row = cursor.fetchone()

    if not row:
        return {key: True for key in USER_PERMISSION_FIELDS}

    return {
        'can_publish': bool(row[0]),
        'can_subscribe': bool(row[1]),
        'can_recharge': bool(row[2]),
        'can_comment': bool(row[3]),
        'can_vote': bool(row[4])
    }


def _user_permission_allowed(user_id, field):
    column = USER_PERMISSION_FIELDS.get(field)
    if not column:
        raise ValueError('Invalid permission field')

    with connection.cursor() as cursor:
        _ensure_user_permission_record(cursor, user_id)
        cursor.execute(f"SELECT {column} FROM user_permissions WHERE user_id = %s", [user_id])
        row = cursor.fetchone()

    return bool(row and row[0])


def _ensure_work_moderation_record(cursor, work_id):
    cursor.execute("SELECT work_id FROM work_moderations WHERE work_id = %s", [work_id])
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO work_moderations (
                work_id, is_hidden, chapters_blocked, updates_blocked,
                subscriptions_blocked, votes_blocked, note, updated_by,
                update_time, create_time
            )
            VALUES (%s, 0, 0, 0, 0, 0, '', NULL, NOW(), NOW())
            """,
            [work_id]
        )


def _ensure_work_moderation_exists(work_id):
    with connection.cursor() as cursor:
        _ensure_work_moderation_record(cursor, work_id)


def _get_work_moderation(work_id):
    with connection.cursor() as cursor:
        _ensure_work_moderation_record(cursor, work_id)
        cursor.execute(
            """
            SELECT is_hidden, chapters_blocked, updates_blocked,
                   subscriptions_blocked, votes_blocked, note
            FROM work_moderations WHERE work_id = %s
            """,
            [work_id]
        )
        row = cursor.fetchone()

    if not row:
        return {
            'is_hidden': False,
            'chapters_blocked': False,
            'updates_blocked': False,
            'subscriptions_blocked': False,
            'votes_blocked': False,
            'note': ''
        }

    return {
        'is_hidden': bool(row[0]),
        'chapters_blocked': bool(row[1]),
        'updates_blocked': bool(row[2]),
        'subscriptions_blocked': bool(row[3]),
        'votes_blocked': bool(row[4]),
        'note': row[5] or ''
    }


def _get_user_display_name(user_id):
    if not user_id:
        return ''

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(r.nickname, u.username, '') AS display_name
            FROM users u
            LEFT JOIN readers r ON u.user_id = r.reader_id
            WHERE u.user_id = %s
            """,
            [user_id]
        )
        row = cursor.fetchone()

    if not row:
        return ''
    display_name = row[0] or ''
    if display_name:
        return display_name
    return f'用户{user_id}'


def _create_message(recipient_id, message_type, content, related_type=None, related_id=None, sender_id=None):
    if not recipient_id:
        return

    resolved_content = (content or '').strip()
    if not resolved_content:
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO messages (sender_id, recipient_id, message_type, content,
                                  related_type, related_id, is_read, send_time)
            VALUES (%s, %s, %s, %s, %s, %s, 0, NOW())
            """,
            [sender_id, recipient_id, message_type, resolved_content, related_type, related_id]
        )


def _send_admin_message(recipient_id, message_type, content, related_type=None, related_id=None, sender_id=None):
    if not recipient_id:
        return

    _create_message(
        recipient_id=recipient_id,
        message_type=message_type,
        content=content or '',
        related_type=related_type,
        related_id=related_id,
        sender_id=sender_id
    )


def _is_admin(user):
    return user and getattr(user, 'role', None) == ADMIN_ROLE


def _record_admin_action(admin_id, target_type, target_id, action, detail=None, request=None, extra=None):
    if not admin_id or not action:
        return

    ip_address = ''
    user_agent = ''
    if request is not None:
        ip_address = _get_client_ip(request)
        user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:512]

    serialized_extra = _serialize_extra(extra)

    resolved_target_type = target_type if target_type is not None else ADMIN_ACTION_TARGET_SYSTEM
    resolved_target_id = target_id if target_id is not None else admin_id

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO admin_action_logs (admin_id, target_type, target_id, action, detail, extra_data, ip_address, user_agent, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            [
                admin_id,
                resolved_target_type,
                resolved_target_id,
                action,
                detail or '',
                serialized_extra,
                ip_address,
                user_agent
            ]
        )


def _record_user_action(user_id, action, target_type=None, target_id=None, detail=None, request=None, extra=None):
    if not user_id or not action:
        return

    ip_address = ''
    user_agent = ''
    if request is not None:
        ip_address = _get_client_ip(request)
        user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:512]

    serialized_extra = _serialize_extra(extra)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_action_logs (user_id, action, target_type, target_id, detail, extra_data, ip_address, user_agent, create_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            [
                user_id,
                action,
                target_type,
                target_id,
                detail or '',
                serialized_extra,
                ip_address,
                user_agent
            ]
        )

def _calculate_word_count(content):
    if not content:
        return 0
    if not isinstance(content, str):
        content = str(content)
    # 简单按字符统计字数
    return len(content.strip())


def calculate_chapter_cost(word_count):
    if not word_count or word_count <= 0:
        return 0
    return max(1, math.ceil(word_count / 200))


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return default


def _get_user_subscription_status(user_id, work_id):
    has_full_subscription = False
    subscribed_chapters = set()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT chapter_id
            FROM subscriptions
            WHERE reader_id = %s AND work_id = %s
            """,
            [user_id, work_id]
        )
        for row in cursor.fetchall():
            chapter_id = row[0]
            if chapter_id is None:
                has_full_subscription = True
            else:
                subscribed_chapters.add(chapter_id)

    return has_full_subscription, subscribed_chapters


def _user_has_subscription(user_id, work_id, chapter_id):
    has_full_subscription, subscribed_chapters = _get_user_subscription_status(user_id, work_id)
    return has_full_subscription or chapter_id in subscribed_chapters


def _record_chapter_reading(user_id, work_id, chapter_id):
    if not user_id:
        return

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT record_id, progress FROM reading_records WHERE reader_id = %s AND chapter_id = %s",
            [user_id, chapter_id]
        )
        existing = cursor.fetchone()

        if existing:
            record_id, progress = existing
            cursor.execute(
                "UPDATE reading_records SET read_time = NOW(), progress = GREATEST(progress, %s), is_finished = CASE WHEN %s >= 100 THEN 1 ELSE is_finished END WHERE record_id = %s",
                [100, 100, record_id]
            )
            return

        cursor.execute(
            """
            INSERT INTO reading_records (reader_id, chapter_id, read_time, progress, is_finished)
            VALUES (%s, %s, NOW(), 100, 1)
            """,
            [user_id, chapter_id]
        )

        cursor.execute(
            "UPDATE works SET read_count = COALESCE(read_count, 0) + 1 WHERE work_id = %s",
            [work_id]
        )

    _record_recommendation_feedback(
        user_id,
        work_id,
        FEEDBACK_EVENT_READ,
        weight_delta=1.0,
        metadata={'chapter_id': chapter_id}
    )


POINT_TRANSACTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS point_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    description VARCHAR(255),
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_time (user_id, create_time)
)
"""


TICKET_WALLET_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_tickets (
    user_id BIGINT PRIMARY KEY,
    ticket_balance INT NOT NULL DEFAULT 0,
    progress DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_earned INT NOT NULL DEFAULT 0,
    total_spent INT NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
"""

COMMENT_LIKES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS comment_likes (
    like_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id BIGINT NOT NULL,
    reader_id BIGINT NOT NULL,
    like_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_comment_reader (comment_id, reader_id),
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    INDEX idx_comment (comment_id),
    INDEX idx_reader (reader_id)
)
"""


SEARCH_RECORDS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS search_records (
    search_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    search_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    search_type TINYINT NOT NULL DEFAULT 1 COMMENT '1=作品搜索，2=作者搜索，3=标签搜索',
    click_work_id BIGINT,
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (click_work_id) REFERENCES works(work_id) ON DELETE SET NULL,
    INDEX idx_reader_time (reader_id, search_time)
)
"""

RECOMMENDATION_FEEDBACK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_recommendation_feedback (
    feedback_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    event_type TINYINT NOT NULL,
    weight DECIMAL(10,4) NOT NULL DEFAULT 1.0,
    event_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE KEY uniq_user_work_event (user_id, work_id, event_type),
    INDEX idx_user_event_time (user_id, event_time),
    INDEX idx_user_event_type (user_id, event_type, event_time),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE
)
"""


def _ensure_point_transactions_table():
    with connection.cursor() as cursor:
        cursor.execute(POINT_TRANSACTIONS_TABLE_SQL)


def _ensure_user_tickets_table():
    with connection.cursor() as cursor:
        cursor.execute(TICKET_WALLET_TABLE_SQL)


def _ensure_user_ticket_wallet(cursor, user_id):
    cursor.execute("SELECT user_id FROM user_tickets WHERE user_id = %s", [user_id])
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO user_tickets (user_id, ticket_balance, progress, total_earned, total_spent)
            VALUES (%s, 0, 0, 0, 0)
            """,
            [user_id]
        )


def _ensure_comment_likes_table():
    with connection.cursor() as cursor:
        cursor.execute(COMMENT_LIKES_TABLE_SQL)


def _ensure_search_records_table():
    with connection.cursor() as cursor:
        cursor.execute(SEARCH_RECORDS_TABLE_SQL)


def _ensure_recommendation_feedback_table():
    with connection.cursor() as cursor:
        cursor.execute(RECOMMENDATION_FEEDBACK_TABLE_SQL)


def _normalize_feedback_weight(value):
    if value is None:
        return FEEDBACK_DEFAULT_WEIGHT
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return FEEDBACK_DEFAULT_WEIGHT
    if math.isnan(numeric) or math.isinf(numeric):
        return FEEDBACK_DEFAULT_WEIGHT
    if numeric == 0:
        return FEEDBACK_DEFAULT_WEIGHT

    abs_value = min(FEEDBACK_MAX_WEIGHT_DELTA, max(FEEDBACK_MIN_WEIGHT_DELTA, abs(numeric)))
    return abs_value if numeric > 0 else -abs_value


def _record_recommendation_feedback(user_id, work_id, event_type, weight_delta=None, metadata=None):
    if not user_id or not work_id or not event_type:
        return

    normalized_delta = _normalize_feedback_weight(weight_delta if weight_delta is not None else FEEDBACK_DEFAULT_WEIGHT)
    if normalized_delta <= 0:
        normalized_delta = FEEDBACK_DEFAULT_WEIGHT

    metadata_value = None
    if metadata not in (None, {}, ''):
        metadata_value = _serialize_extra(metadata)

    _ensure_recommendation_feedback_table()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO user_recommendation_feedback (user_id, work_id, event_type, weight, event_time, metadata)
            VALUES (%s, %s, %s, %s, NOW(), %s)
            ON DUPLICATE KEY UPDATE
                weight = LEAST(weight + VALUES(weight), %s),
                event_time = CASE WHEN VALUES(weight) > 0 THEN GREATEST(event_time, VALUES(event_time)) ELSE event_time END,
                metadata = CASE WHEN VALUES(weight) > 0 THEN COALESCE(VALUES(metadata), metadata) ELSE metadata END
            """,
            [user_id, work_id, event_type, normalized_delta, metadata_value, FEEDBACK_MAX_AGG_WEIGHT]
        )

        cutoff_time = datetime.utcnow() - timedelta(days=FEEDBACK_RETENTION_DAYS)
        cursor.execute(
            """
            DELETE FROM user_recommendation_feedback
            WHERE user_id = %s AND event_time < %s
            """,
            [user_id, cutoff_time]
        )


def _fetch_user_search_history(user_id, limit=20):
    limit_value = max(1, min(int(limit or 20), 100))
    _ensure_search_records_table()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT keyword, search_time, search_type
            FROM search_records
            WHERE reader_id = %s
            ORDER BY search_time DESC
            LIMIT %s
            """,
            [user_id, limit_value]
        )
        history = []
        seen_keywords = set()
        for keyword, search_time, search_type in cursor.fetchall():
            normalized_keyword = (keyword or '').strip()
            if normalized_keyword.lower() in seen_keywords:
                continue
            seen_keywords.add(normalized_keyword.lower())
            history.append({
                'keyword': keyword,
                'search_time': search_time.isoformat() if search_time else None,
                'search_type': int(search_type or 1),
            })
        return history


PREFERENCE_WEIGHT_MAP = {
    'collection': 3.0,
    'reading': 1.5,
    'vote': 2.5,
    'subscription': 3.0,
    'feedback': 1.0,
}


def _parse_tags_field(tags_field):
    if not tags_field:
        return []

    if isinstance(tags_field, list):
        return [str(tag).strip() for tag in tags_field if str(tag).strip()]

    if isinstance(tags_field, str):
        try:
            parsed = json.loads(tags_field)
            if isinstance(parsed, list):
                return [str(tag).strip() for tag in parsed if str(tag).strip()]
        except (json.JSONDecodeError, TypeError):
            pass

        separators = [',', '，', ';', '；', '|', '/', ' ']
        fragments = [tags_field]
        for sep in separators:
            temp = []
            for fragment in fragments:
                temp.extend(fragment.split(sep))
            fragments = temp
        return [frag.strip() for frag in fragments if frag.strip()]

    return []


def _normalize_tag(tag):
    if tag is None:
        return ''
    if not isinstance(tag, str):
        tag = str(tag)
    return tag.strip().lower()


def _get_top_keys(score_map, limit=3):
    sorted_items = sorted(score_map.items(), key=lambda item: (-item[1], item[0]))
    return [item[0] for item in sorted_items[:limit]]


def _get_category_names(category_ids):
    if not category_ids:
        return {}
    placeholders = ','.join(['%s'] * len(category_ids))
    query = f"SELECT category_id, name FROM categories WHERE category_id IN ({placeholders})"
    with connection.cursor() as cursor:
        cursor.execute(query, list(category_ids))
        return {int(row[0]): row[1] for row in cursor.fetchall() if row[0] is not None}


def _get_top_categories_by_popularity(limit=3):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT w.category_id,
                   SUM(COALESCE(w.vote_count, 0)) * 3 +
                   SUM(COALESCE(w.collect_count, 0)) * 2 +
                   SUM(COALESCE(w.read_count, 0)) AS popularity
            FROM works w
            WHERE w.status IN (1, 2)
            GROUP BY w.category_id
            ORDER BY popularity DESC
            LIMIT %s
            """,
            [limit]
        )
        return [int(row[0]) for row in cursor.fetchall() if row[0] is not None]


def _get_user_preference_scores(user_id):
    category_scores = defaultdict(float)
    tag_scores = defaultdict(float)
    tag_display_map = {}
    has_personal_signal = False

    with connection.cursor() as cursor:
        # 收藏偏好
        cursor.execute(
            """
            SELECT w.category_id, w.tags
            FROM collections c
            JOIN works w ON c.work_id = w.work_id
            WHERE c.reader_id = %s
            """,
            [user_id]
        )
        for category_id, tags_field in cursor.fetchall():
            has_personal_signal = True
            score = PREFERENCE_WEIGHT_MAP['collection']
            if category_id is not None:
                category_scores[int(category_id)] += score
            for tag in _parse_tags_field(tags_field):
                normalized = _normalize_tag(tag)
                if normalized:
                    tag_scores[normalized] += score
                    tag_display_map.setdefault(normalized, tag)

        # 阅读偏好
        cursor.execute(
            """
            SELECT w.category_id, w.tags, COUNT(DISTINCT rr.chapter_id) AS cnt
            FROM reading_records rr
            JOIN chapters ch ON rr.chapter_id = ch.chapter_id
            JOIN works w ON ch.work_id = w.work_id
            WHERE rr.reader_id = %s
            GROUP BY w.work_id, w.category_id, w.tags
            """,
            [user_id]
        )
        for category_id, tags_field, cnt in cursor.fetchall():
            has_personal_signal = True
            base = PREFERENCE_WEIGHT_MAP['reading']
            score = base * max(1.0, math.sqrt(float(cnt) if cnt else 1.0))
            if category_id is not None:
                category_scores[int(category_id)] += score
            for tag in _parse_tags_field(tags_field):
                normalized = _normalize_tag(tag)
                if normalized:
                    tag_scores[normalized] += score
                    tag_display_map.setdefault(normalized, tag)

        # 投票偏好
        cursor.execute(
            """
            SELECT w.category_id, w.tags, COALESCE(SUM(v.count), 0) AS cnt
            FROM votes v
            JOIN works w ON v.work_id = w.work_id
            WHERE v.reader_id = %s
            GROUP BY w.work_id, w.category_id, w.tags
            """,
            [user_id]
        )
        for category_id, tags_field, cnt in cursor.fetchall():
            has_personal_signal = True
            base = PREFERENCE_WEIGHT_MAP['vote']
            score = base * max(1.0, float(cnt) if cnt else 1.0)
            if category_id is not None:
                category_scores[int(category_id)] += score
            for tag in _parse_tags_field(tags_field):
                normalized = _normalize_tag(tag)
                if normalized:
                    tag_scores[normalized] += score
                    tag_display_map.setdefault(normalized, tag)

        # 订阅偏好
        cursor.execute(
            """
            SELECT w.category_id, w.tags, COUNT(*) AS cnt
            FROM subscriptions s
            JOIN works w ON s.work_id = w.work_id
            WHERE s.reader_id = %s
            GROUP BY w.work_id, w.category_id, w.tags
            """,
            [user_id]
        )
        for category_id, tags_field, cnt in cursor.fetchall():
            has_personal_signal = True
            base = PREFERENCE_WEIGHT_MAP['subscription']
            score = base * max(1.0, float(cnt) if cnt else 1.0)
            if category_id is not None:
                category_scores[int(category_id)] += score
            for tag in _parse_tags_field(tags_field):
                normalized = _normalize_tag(tag)
                if normalized:
                    tag_scores[normalized] += score
                    tag_display_map.setdefault(normalized, tag)

        _ensure_recommendation_feedback_table()
        cursor.execute(
            """
            SELECT w.category_id, w.tags, f.event_type, f.weight, f.event_time
            FROM user_recommendation_feedback f
            JOIN works w ON f.work_id = w.work_id
            WHERE f.user_id = %s
            """,
            [user_id]
        )
        for category_id, tags_field, event_type, weight_value, event_time in cursor.fetchall():
            has_personal_signal = True
            event_type_int = int(event_type or 0)
            base = FEEDBACK_EVENT_WEIGHTS.get(event_type_int)
            if not base:
                continue

            try:
                weight_float = float(weight_value or 0.0)
            except (TypeError, ValueError, InvalidOperation):
                weight_float = 0.0

            if weight_float <= 0:
                continue

            decay = 1.0
            event_dt = event_time
            if isinstance(event_dt, datetime):
                if timezone.is_aware(event_dt):
                    event_dt = timezone.make_naive(event_dt)
                age_days = max(0, (datetime.utcnow() - event_dt.replace(tzinfo=None)).days)
                if FEEDBACK_DECAY_DAYS > 0 and age_days > 0:
                    decay = max(0.2, 1.0 - age_days / FEEDBACK_DECAY_DAYS)

            score = base * weight_float * decay * PREFERENCE_WEIGHT_MAP['feedback']

            if category_id is not None:
                try:
                    category_scores[int(category_id)] += score
                except (TypeError, ValueError):
                    pass

            for tag in _parse_tags_field(tags_field):
                normalized = _normalize_tag(tag)
                if normalized:
                    tag_scores[normalized] += score
                    tag_display_map.setdefault(normalized, tag)

    return category_scores, tag_scores, tag_display_map, has_personal_signal


def _serialize_work_row(row):
    work = {
        'work_id': row[0],
        'title': row[1],
        'cover_url': row[2],
        'intro': row[3] or '',
        'tags': _parse_tags_field(row[4]),
        'category_id': row[5],
        'category_name': row[6] or '',
        'read_count': int(row[7] or 0),
        'collect_count': int(row[8] or 0),
        'vote_count': int(row[9] or 0),
        'update_time': row[10].isoformat() if row[10] else None,
        'author_name': row[11] or '',
    }
    work['rating'] = None
    return work


def _fetch_candidate_works(category_ids=None, limit=30, exclude_ids=None):
    params = []
    exclude_ids = set(exclude_ids or [])
    query = """
        SELECT w.work_id, w.title, w.cover_url, w.intro, w.tags,
               w.category_id, COALESCE(c.name, '') AS category_name,
               COALESCE(w.read_count, 0) AS read_count,
               COALESCE(w.collect_count, 0) AS collect_count,
               COALESCE(w.vote_count, 0) AS vote_count,
               w.update_time,
               COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name
        FROM works w
        LEFT JOIN authors a ON w.author_id = a.author_id
        LEFT JOIN readers r ON w.author_id = r.reader_id
        LEFT JOIN users u ON w.author_id = u.user_id
        LEFT JOIN categories c ON w.category_id = c.category_id
        WHERE w.status IN (1, 2)
    """
    if category_ids:
        placeholders = ','.join(['%s'] * len(category_ids))
        query += f" AND w.category_id IN ({placeholders})"
        params.extend(category_ids)

    query += """
        ORDER BY w.vote_count DESC, w.collect_count DESC, w.read_count DESC, w.update_time DESC
        LIMIT %s
    """
    params.append(max(limit, len(exclude_ids) + limit))

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            work_id = row[0]
            if work_id in exclude_ids:
                continue
            results.append(_serialize_work_row(row))
            if len(results) >= limit:
                break
        return results


def _score_work_for_preferences(work, category_scores, tag_scores):
    score = category_scores.get(int(work.get('category_id') or 0), 0.0)
    work_tags = work.get('tags') or []
    tag_score = 0.0
    for tag in work_tags:
        normalized = _normalize_tag(tag)
        if normalized in tag_scores:
            tag_score += tag_scores[normalized]
    score += tag_score

    # 结合作品热度
    score += min(work.get('vote_count', 0) / 5.0, 20)
    score += min(work.get('collect_count', 0) / 10.0, 15)
    score += min(work.get('read_count', 0) / 2000.0, 15)

    # 更新时间加权
    if work.get('update_time'):
        try:
            update_dt = datetime.fromisoformat(work['update_time'])
            age_days = (datetime.utcnow() - update_dt).days
            freshness_bonus = max(0, 10 - age_days)
            score += freshness_bonus
        except ValueError:
            pass

    return score


def _build_favorite_type_recommendations(category_scores, tag_scores, fallback_categories, top_tags=None, limit=9):
    effective_category_scores = defaultdict(float)
    for key, value in category_scores.items():
        try:
            effective_category_scores[int(key)] += float(value)
        except (TypeError, ValueError):
            continue

    if not effective_category_scores and fallback_categories:
        for cat_id in fallback_categories:
            try:
                effective_category_scores[int(cat_id)] += 1.0
            except (TypeError, ValueError):
                continue

    effective_tag_scores = defaultdict(float)
    for key, value in tag_scores.items():
        if not key:
            continue
        effective_tag_scores[key] += float(value)

    active_category_ids = list(effective_category_scores.keys()) or fallback_categories
    candidates = _fetch_candidate_works(active_category_ids, limit=60)
    if not candidates:
        candidates = _fetch_candidate_works(None, limit=60)

    filtered_candidates = candidates
    normalized_top_tags = set(_normalize_tag(tag) for tag in (top_tags or []) if tag)
    if normalized_top_tags:
        tagged = []
        for work in candidates:
            work_tags = {_normalize_tag(tag) for tag in (work.get('tags') or []) if tag}
            if work_tags & normalized_top_tags:
                tagged.append(work)
        if tagged:
            filtered_candidates = tagged

    scored = []
    for work in filtered_candidates:
        work_score = _score_work_for_preferences(work, effective_category_scores, effective_tag_scores)
        scored.append((work_score, work))

    scored.sort(key=lambda item: item[0], reverse=True)
    unique = OrderedDict()
    for _, work in scored:
        unique.setdefault(work['work_id'], work)
        if len(unique) >= limit:
            break

    results = list(unique.values())
    if not results:
        results = _fetch_candidate_works(None, limit=limit, exclude_ids=set())
    return results


def _fetch_search_based_recommendations(user_id, fallback_categories, limit=8, exclude_ids=None):
    _ensure_search_records_table()
    exclude_ids = set(exclude_ids or [])
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT keyword, search_time
            FROM search_records
            WHERE reader_id = %s
            ORDER BY search_time DESC
            LIMIT 5
            """,
            [user_id]
        )
        keyword_rows = cursor.fetchall()

    if not keyword_rows:
        return [], False

    recommendations = OrderedDict()
    with connection.cursor() as cursor:
        for index, (keyword, _search_time) in enumerate(keyword_rows):
            if not keyword:
                continue
            like_keyword = f"%{keyword}%"
            cursor.execute(
                """
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.tags,
                       w.category_id, COALESCE(c.name, '') AS category_name,
                       COALESCE(w.read_count, 0) AS read_count,
                       COALESCE(w.collect_count, 0) AS collect_count,
                       COALESCE(w.vote_count, 0) AS vote_count,
                       w.update_time,
                       COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name
                FROM works w
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN readers r ON w.author_id = r.reader_id
                LEFT JOIN users u ON w.author_id = u.user_id
                LEFT JOIN categories c ON w.category_id = c.category_id
                WHERE w.status IN (1, 2)
                  AND (
                        w.title LIKE %s OR
                        w.intro LIKE %s OR
                        COALESCE(a.pen_name, r.nickname, u.username, '') LIKE %s OR
                        COALESCE(w.tags, '') LIKE %s
                  )
                ORDER BY w.vote_count DESC, w.read_count DESC, w.update_time DESC
                LIMIT 8
                """,
                [like_keyword, like_keyword, like_keyword, like_keyword]
            )
            weight = max(1, 5 - index)
            for row in cursor.fetchall():
                work = _serialize_work_row(row)
                if work['work_id'] in exclude_ids:
                    continue
                current = recommendations.get(work['work_id'])
                if current:
                    current.setdefault('_score', 0)
                    current['_score'] += weight
                else:
                    work['_score'] = weight
                    recommendations[work['work_id']] = work
                if len(recommendations) >= limit * 2:
                    break
            if len(recommendations) >= limit * 2:
                break

    sorted_recs = sorted(
        recommendations.values(),
        key=lambda item: (-item.get('_score', 0), -item.get('vote_count', 0), -item.get('read_count', 0))
    )
    trimmed = []
    for work in sorted_recs:
        work.pop('_score', None)
        trimmed.append(work)
        if len(trimmed) >= limit:
            break

    if len(trimmed) < limit:
        exclude_ids.update({w['work_id'] for w in trimmed})
        extra = []
        if fallback_categories:
            extra = _fetch_candidate_works(fallback_categories, limit=limit, exclude_ids=exclude_ids)
        if not extra:
            extra = _fetch_candidate_works(None, limit=limit, exclude_ids=exclude_ids)
        existing_ids = {w['work_id'] for w in trimmed}
        for work in extra:
            if work['work_id'] not in existing_ids:
                trimmed.append(work)
                if len(trimmed) >= limit:
                    break
    return trimmed, True


def _build_favorite_rank_recommendations(category_ids, limit_per_category=4, exclude_ids=None):
    if not category_ids:
        category_ids = _get_top_categories_by_popularity(limit=3)

    ordered_categories = list(category_ids or [])
    category_names = _get_category_names(ordered_categories)
    exclude_ids = set(exclude_ids or [])
    seen_ids = set(exclude_ids)
    recommendations = []

    expected_total = limit_per_category * max(1, len(ordered_categories) or 1)

    with connection.cursor() as cursor:
        general_rank_rows = None

        def fetch_ranking_rows(target_category_id, fetch_limit):
            params = []
            if target_category_id is None:
                category_condition = "AND rk.category_id IS NULL"
            else:
                category_condition = "AND rk.category_id = %s"
                params.append(target_category_id)

            query = f"""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.tags,
                       w.category_id, COALESCE(c.name, '') AS category_name,
                       COALESCE(w.read_count, 0) AS read_count,
                       COALESCE(w.collect_count, 0) AS collect_count,
                       COALESCE(w.vote_count, 0) AS vote_count,
                       w.update_time,
                       COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name
                FROM rankings rk
                JOIN ranking_details rd ON rk.ranking_id = rd.ranking_id
                JOIN works w ON rd.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN readers r ON w.author_id = r.reader_id
                LEFT JOIN users u ON w.author_id = u.user_id
                LEFT JOIN categories c ON w.category_id = c.category_id
                WHERE w.status IN (1, 2)
                  AND rk.status = 1
                  AND rd.stat_date = (
                      SELECT MAX(rd2.stat_date)
                      FROM ranking_details rd2
                      WHERE rd2.ranking_id = rk.ranking_id
                  )
                  {category_condition}
                ORDER BY rd.rank ASC, rd.score DESC, w.update_time DESC
                LIMIT %s
            """
            params.append(fetch_limit)
            cursor.execute(query, params)
            return cursor.fetchall()

        for raw_category_id in ordered_categories:
            rows = fetch_ranking_rows(raw_category_id, limit_per_category * 3)
            if not rows:
                if general_rank_rows is None:
                    general_rank_rows = fetch_ranking_rows(None, limit_per_category * 4)
                rows = general_rank_rows or []

            picked = 0
            display_name = ''
            try:
                if raw_category_id is not None:
                    display_name = category_names.get(int(raw_category_id), '')
            except (TypeError, ValueError):
                display_name = ''

            for row in rows:
                work = _serialize_work_row(row)
                work_id = work['work_id']
                if work_id in seen_ids:
                    continue
                seen_ids.add(work_id)
                if display_name:
                    work['category_name'] = display_name
                recommendations.append(work)
                picked += 1
                if picked >= limit_per_category:
                    break

    if len(recommendations) < expected_total:
        remaining = expected_total - len(recommendations)
        fallback_categories = ordered_categories or None
        extra_candidates = _fetch_candidate_works(
            fallback_categories,
            limit=remaining,
            exclude_ids=seen_ids
        )
        for work in extra_candidates:
            work_id = work['work_id']
            if work_id in seen_ids:
                continue
            seen_ids.add(work_id)
            recommendations.append(work)
            if len(recommendations) >= expected_total:
                break

    if not recommendations:
        recommendations = _fetch_candidate_works(None, limit=limit_per_category * 2, exclude_ids=exclude_ids)

    return recommendations

# 用户认证相关API
@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def user_register(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        role = int(data.get('role', 1))  # 默认为读者
        phone = data.get('phone')
        email = data.get('email')
        
        if not username or not password:
            return JsonResponse({'success': False, 'error': '用户名和密码不能为空'})

        if role == ADMIN_ROLE:
            return JsonResponse({'success': False, 'error': '请通过管理员通道注册管理员账号'})

        if role not in (1, 2, 3):
            return JsonResponse({'success': False, 'error': '无效的角色类型'})
        
        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT user_id FROM users WHERE username = %s", [username])
            if cursor.fetchone():
                return JsonResponse({'success': False, 'error': '用户名已存在'})
            
            # 检查手机号是否已存在（只检查非空值）
            if phone and phone.strip():
                cursor.execute("SELECT user_id FROM users WHERE phone = %s AND phone IS NOT NULL AND phone != ''", [phone])
                if cursor.fetchone():
                    return JsonResponse({'success': False, 'error': '手机号已被使用'})
            
            # 检查邮箱是否已存在（只检查非空值）
            if email and email.strip():
                cursor.execute("SELECT user_id FROM users WHERE email = %s AND email IS NOT NULL AND email != ''", [email])
                if cursor.fetchone():
                    return JsonResponse({'success': False, 'error': '邮箱已被使用'})
            
            # 插入新用户，空字符串转换为NULL
            hashed_password = hash_password(password)
            phone_value = phone if phone and phone.strip() else None
            email_value = email if email and email.strip() else None
            
            cursor.execute("""
                INSERT INTO users (username, password, role, phone, email, status, create_time)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
            """, [username, hashed_password, role, phone_value, email_value])
            
            user_id = cursor.lastrowid
            
            # 根据角色插入对应信息表
            if role == 1:  # 读者
                nickname = data.get('nickname', username)
                cursor.execute("""
                    INSERT INTO readers (reader_id, nickname, balance)
                    VALUES (%s, %s, 0)
                """, [user_id, nickname])
                # 为读者也创建作者记录，以便可以创建作品
                cursor.execute("""
                    INSERT INTO authors (author_id, pen_name, intro, identity_status, total_income)
                    VALUES (%s, %s, '', 0, 0)
                """, [user_id, username])
            elif role == 2:  # 作者
                pen_name = data.get('pen_name', username)
                cursor.execute("""
                    INSERT INTO authors (author_id, pen_name, intro, identity_status, total_income)
                    VALUES (%s, %s, '', 0, 0)
                """, [user_id, pen_name])
            elif role == 3:  # 编辑
                real_name = data.get('real_name', username)
                department = data.get('department', '')
                position = data.get('position', '')
                cursor.execute("""
                    INSERT INTO editors (editor_id, real_name, department, position)
                    VALUES (%s, %s, %s, %s)
                """, [user_id, real_name, department, position])
                # 为编辑也创建作者记录，以便可以创建作品
                cursor.execute("""
                    INSERT INTO authors (author_id, pen_name, intro, identity_status, total_income)
                    VALUES (%s, %s, '', 0, 0)
                """, [user_id, real_name])

            _ensure_user_permission_record(cursor, user_id)
            
            return JsonResponse({'success': True, 'message': '注册成功'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@csrf_exempt
def user_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'success': False, 'error': '用户名和密码不能为空'})
        
        with connection.cursor() as cursor:
            hashed_password = hash_password(password)
            cursor.execute("""
                SELECT user_id, username, role, status 
                FROM users 
                WHERE username = %s AND password = %s
            """, [username, hashed_password])
            
            user_data = cursor.fetchone()
            if not user_data:
                return JsonResponse({'success': False, 'error': '用户名或密码错误'})
            
            if user_data[3] != 1:  # status != 1
                return JsonResponse({'success': False, 'error': '账号已被禁用'})
            
            # 更新最后登录时间
            cursor.execute("""
                UPDATE users SET last_login_time = NOW() WHERE user_id = %s
            """, [user_data[0]])
            
            token = generate_token(user_data[0], user_data[2])
            
            return JsonResponse({
                'success': True,
                'token': token,
                'user_id': user_data[0],
                'username': user_data[1],
                'role': user_data[2]
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def admin_register(request):
    try:
        data = json.loads(request.body)
        secret_key = data.get('secret_key')
        if secret_key != ADMIN_REGISTRATION_KEY:
            return JsonResponse({'success': False, 'error': '管理员密钥无效'}, status=403)

        username = data.get('username')
        password = data.get('password')
        display_name = data.get('display_name') or username
        phone = data.get('phone')
        email = data.get('email')

        if not username or not password:
            return JsonResponse({'success': False, 'error': '用户名和密码不能为空'}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE username = %s", [username])
            if cursor.fetchone():
                return JsonResponse({'success': False, 'error': '用户名已存在'}, status=400)

            if phone and phone.strip():
                cursor.execute("SELECT 1 FROM users WHERE phone = %s", [phone])
                if cursor.fetchone():
                    return JsonResponse({'success': False, 'error': '手机号已被使用'}, status=400)

            if email and email.strip():
                cursor.execute("SELECT 1 FROM users WHERE email = %s", [email])
                if cursor.fetchone():
                    return JsonResponse({'success': False, 'error': '邮箱已被使用'}, status=400)

            hashed_password = hash_password(password)
            phone_value = phone if phone and phone.strip() else None
            email_value = email if email and email.strip() else None

            cursor.execute(
                """
                INSERT INTO users (username, password, role, phone, email, status, create_time)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
                """,
                [username, hashed_password, ADMIN_ROLE, phone_value, email_value]
            )

            admin_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO admins (admin_id, display_name, status, create_time, update_time)
                VALUES (%s, %s, 1, NOW(), NOW())
                """,
                [admin_id, display_name]
            )

            _ensure_user_permission_record(cursor, admin_id)

        detail = f"管理员账号注册：用户名={username}"
        _record_admin_action(admin_id, ADMIN_ACTION_TARGET_SYSTEM, admin_id, 'admin_register', detail, request=request, extra={'username': username})
        return JsonResponse({'success': True, 'message': '管理员注册成功'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def admin_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'success': False, 'error': '用户名和密码不能为空'}, status=400)

        with connection.cursor() as cursor:
            hashed_password = hash_password(password)
            cursor.execute(
                """
                SELECT user_id, username, role, status
                FROM users
                WHERE username = %s AND password = %s AND role = %s
                """,
                [username, hashed_password, ADMIN_ROLE]
            )

            row = cursor.fetchone()
            if not row:
                return JsonResponse({'success': False, 'error': '账号或密码错误'}, status=400)

            if row[3] != 1:
                return JsonResponse({'success': False, 'error': '管理员账号已被禁用'}, status=403)

            cursor.execute("UPDATE users SET last_login_time = NOW() WHERE user_id = %s", [row[0]])

        token = generate_token(row[0], row[2])
        _record_admin_action(row[0], ADMIN_ACTION_TARGET_SYSTEM, row[0], 'admin_login', '管理员登录成功', request=request)
        return JsonResponse({
            'success': True,
            'token': token,
            'user_id': row[0],
            'username': row[1],
            'role': row[2]
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_users(request):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    search = (request.GET.get('search') or '').strip()
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    page = max(1, int(request.GET.get('page', 1) or 1))
    page_size = int(request.GET.get('page_size', 20) or 20)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    conditions = ['u.role <> %s']
    params = [ADMIN_ROLE]

    if search:
        like_value = f"%{search}%"
        conditions.append("(u.username LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)")
        params.extend([like_value, like_value, like_value])

    if role_filter not in (None, '', 'all'):
        if role_filter in ('normal', 'user', 'reader_author'):
            conditions.append('u.role IN (1, 2)')
        else:
            try:
                role_value = int(role_filter)
                conditions.append('u.role = %s')
                params.append(role_value)
            except (TypeError, ValueError):
                pass

    if status_filter not in (None, '', 'all'):
        try:
            status_value = int(status_filter)
            conditions.append('u.status = %s')
            params.append(status_value)
        except (TypeError, ValueError):
            pass

    where_clause = ' AND '.join(conditions) if conditions else '1=1'

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM users u WHERE {where_clause}", params)
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        cursor.execute(
            f"""
            SELECT u.user_id, u.username, u.role, u.status, u.create_time, u.last_login_time,
                   u.email, u.phone,
                   COALESCE(up.can_publish, 1) AS can_publish,
                   COALESCE(up.can_subscribe, 1) AS can_subscribe,
                   COALESCE(up.can_recharge, 1) AS can_recharge,
                   COALESCE(up.can_comment, 1) AS can_comment,
                   COALESCE(up.can_vote, 1) AS can_vote
            FROM users u
            LEFT JOIN user_permissions up ON u.user_id = up.user_id
            WHERE {where_clause}
            ORDER BY u.create_time DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset]
        )

        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'role': row[2],
                'status': row[3],
                'create_time': row[4].isoformat() if row[4] else None,
                'last_login_time': row[5].isoformat() if row[5] else None,
                'email': row[6],
                'phone': row[7],
                'permissions': {
                    'can_publish': bool(row[8]),
                    'can_subscribe': bool(row[9]),
                    'can_recharge': bool(row[10]),
                    'can_comment': bool(row[11]),
                    'can_vote': bool(row[12])
                }
            })

    return Response({'success': True, 'users': users, 'total': total})


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_user_permissions(request, user_id):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    try:
        target_permissions = _get_user_permissions(user_id)
    except Exception:
        target_permissions = {key: True for key in USER_PERMISSION_FIELDS}

    data = request.data or {}
    reason = (data.get('reason') or '').strip()
    status_value = data.get('status')

    permission_updates = {}
    for key in USER_PERMISSION_FIELDS:
        if key in data:
            permission_updates[key] = bool(data.get(key))

    if status_value not in (None, ''):
        try:
            status_value = int(status_value)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': '状态值无效'}, status=status.HTTP_400_BAD_REQUEST)
        if status_value not in (0, 1):
            return Response({'success': False, 'error': '状态值仅支持0或1'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        status_value = None

    if not permission_updates and status_value is None:
        return Response({'success': False, 'error': '未指定任何可更新的字段'}, status=status.HTTP_400_BAD_REQUEST)

    with connection.cursor() as cursor:
        cursor.execute("SELECT username, role, status FROM users WHERE user_id = %s", [user_id])
        user_row = cursor.fetchone()
        if not user_row:
            return Response({'success': False, 'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if user_row[1] == ADMIN_ROLE:
            return Response({'success': False, 'error': '无法直接修改管理员账号'}, status=status.HTTP_400_BAD_REQUEST)

        messages = []
        permission_sql_parts = []
        permission_params = []

        for key, enabled in permission_updates.items():
            column = USER_PERMISSION_FIELDS[key]
            new_value = 1 if enabled else 0
            if target_permissions.get(key) == enabled:
                continue
            permission_sql_parts.append(f"{column} = %s")
            permission_params.append(new_value)
            action_text = '已恢复' if enabled else '已暂停'
            messages.append(f"{USER_PERMISSION_LABELS[key]}权限{action_text}")

        if permission_sql_parts:
            permission_sql_parts.append("update_time = NOW()")
            update_sql = ", ".join(permission_sql_parts)
            cursor.execute(
                f"UPDATE user_permissions SET {update_sql} WHERE user_id = %s",
                permission_params + [user_id]
            )

        status_changed = False
        if status_value is not None and status_value != user_row[2]:
            cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", [status_value, user_id])
            status_changed = True
            if status_value == 1:
                messages.append('账号状态已恢复正常')
            else:
                messages.append('账号状态已被禁用')

    if messages:
        message_lines = ['管理员已调整您的账号权限：']
        for msg in messages:
            message_lines.append(f"- {msg}")
        if reason:
            message_lines.append(f"原因：{reason}")
        _send_admin_message(user_id, ADMIN_MESSAGE_TYPE_USER, '\n'.join(message_lines), related_type=1)

    if messages:
        detail_lines = list(messages)
        if reason:
            detail_lines.append(f"原因：{reason}")
        _record_admin_action(request.user.user_id, ADMIN_ACTION_TARGET_USER, user_id, 'update_user_permissions', '\n'.join(detail_lines), request=request)

    return Response({'success': True, 'message': '操作成功', 'status_changed': bool(status_changed), 'updates': list(messages)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_works(request):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    search = (request.GET.get('search') or '').strip()
    status_filter = request.GET.get('status')
    page = max(1, int(request.GET.get('page', 1) or 1))
    page_size = int(request.GET.get('page_size', 20) or 20)
    page_size = min(max(page_size, 1), 50)
    offset = (page - 1) * page_size

    conditions = ['1=1']
    params = []

    if search:
        like_value = f"%{search}%"
        conditions.append("(w.title LIKE %s OR COALESCE(a.pen_name, r.nickname, u.username, '') LIKE %s)")
        params.extend([like_value, like_value])

    if status_filter not in (None, '', 'all'):
        try:
            status_value = int(status_filter)
            conditions.append('w.status = %s')
            params.append(status_value)
        except (TypeError, ValueError):
            pass

    where_clause = ' AND '.join(conditions)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM works w
            WHERE {where_clause}
            """,
            params
        )
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        cursor.execute(
            f"""
            SELECT w.work_id, w.title, w.status, w.create_time, w.update_time,
                   w.author_id,
                   COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name,
                   COALESCE(wm.is_hidden, 0),
                   COALESCE(wm.chapters_blocked, 0),
                   COALESCE(wm.updates_blocked, 0),
                   COALESCE(wm.subscriptions_blocked, 0),
                   COALESCE(wm.votes_blocked, 0),
                   COALESCE(wm.note, '')
            FROM works w
            LEFT JOIN work_moderations wm ON w.work_id = wm.work_id
            LEFT JOIN authors a ON w.author_id = a.author_id
            LEFT JOIN readers r ON w.author_id = r.reader_id
            LEFT JOIN users u ON w.author_id = u.user_id
            WHERE {where_clause}
            ORDER BY w.update_time DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset]
        )

        works = []
        for row in cursor.fetchall():
            works.append({
                'work_id': row[0],
                'title': row[1],
                'status': row[2],
                'create_time': row[3].isoformat() if row[3] else None,
                'update_time': row[4].isoformat() if row[4] else None,
                'author_id': row[5],
                'author_name': row[6],
                'moderation': {
                    'is_hidden': bool(row[7]),
                    'chapters_blocked': bool(row[8]),
                    'updates_blocked': bool(row[9]),
                    'subscriptions_blocked': bool(row[10]),
                    'votes_blocked': bool(row[11]),
                    'note': row[12]
                }
            })

    return Response({'success': True, 'works': works, 'total': total})


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_work_moderation(request, work_id):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data or {}
    reason = (data.get('reason') or '').strip()
    status_value = data.get('status')

    moderation_updates = {}
    for key in WORK_MODERATION_FIELDS:
        if key in data:
            if key == 'note':
                moderation_updates[key] = data.get(key) or ''
            else:
                moderation_updates[key] = bool(data.get(key))

    if status_value not in (None, ''):
        try:
            status_value = int(status_value)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': '作品状态值无效'}, status=status.HTTP_400_BAD_REQUEST)
        if status_value not in (0, 1, 2, 3):
            return Response({'success': False, 'error': '作品状态值仅支持0/1/2/3'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        status_value = None

    if not moderation_updates and status_value is None:
        return Response({'success': False, 'error': '未指定任何可更新字段'}, status=status.HTTP_400_BAD_REQUEST)

    messages = []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT w.title, w.author_id, w.status,
                   COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name
            FROM works w
            LEFT JOIN authors a ON w.author_id = a.author_id
            LEFT JOIN readers r ON w.author_id = r.reader_id
            LEFT JOIN users u ON w.author_id = u.user_id
            WHERE w.work_id = %s
            """,
            [work_id]
        )
        work_row = cursor.fetchone()
        if not work_row:
            return Response({'success': False, 'error': '作品不存在'}, status=status.HTTP_404_NOT_FOUND)

        work_title, author_id, current_status, author_name = work_row

        _ensure_work_moderation_record(cursor, work_id)
        cursor.execute(
            """
            SELECT is_hidden, chapters_blocked, updates_blocked,
                   subscriptions_blocked, votes_blocked, note
            FROM work_moderations WHERE work_id = %s
            """,
            [work_id]
        )
        moderation_row = cursor.fetchone()
        current_moderation = {
            'is_hidden': bool(moderation_row[0]),
            'chapters_blocked': bool(moderation_row[1]),
            'updates_blocked': bool(moderation_row[2]),
            'subscriptions_blocked': bool(moderation_row[3]),
            'votes_blocked': bool(moderation_row[4]),
            'note': moderation_row[5] or ''
        }

        set_parts = []
        params = []

        for key, value in moderation_updates.items():
            column = WORK_MODERATION_FIELDS[key]
            if key == 'note':
                if value == current_moderation.get(key, ''):
                    continue
                set_parts.append("note = %s")
                params.append(value)
                messages.append('备注信息已更新')
            else:
                bool_value = 1 if value else 0
                if current_moderation.get(key) == value:
                    continue
                set_parts.append(f"{column} = %s")
                params.append(bool_value)
                action_text = '已开放' if value is False else '已限制'
                messages.append(f"{WORK_MODERATION_LABELS[key]} {action_text}")

        if set_parts:
            set_parts.append("updated_by = %s")
            params.append(request.user.user_id)
            set_parts.append("update_time = NOW()")
            update_sql = ", ".join(set_parts)
            cursor.execute(
                f"UPDATE work_moderations SET {update_sql} WHERE work_id = %s",
                params + [work_id]
            )

        status_changed = False
        if status_value is not None and status_value != current_status:
            cursor.execute("UPDATE works SET status = %s WHERE work_id = %s", [status_value, work_id])
            status_changed = True
            if status_value == 3:
                messages.append('作品已被屏蔽下架')
            elif status_value == 1:
                messages.append('作品状态已恢复为连载中')
            elif status_value == 2:
                messages.append('作品状态已调整为完结')
            elif status_value == 0:
                messages.append('作品状态已调整为草稿')

    if messages:
        message_lines = [f"《{work_title}》的状态已由管理员调整："]
        for msg in messages:
            message_lines.append(f"- {msg}")
        if reason:
            message_lines.append(f"原因：{reason}")
        _send_admin_message(author_id, ADMIN_MESSAGE_TYPE_WORK, '\n'.join(message_lines), related_type=2, related_id=work_id)

    if messages:
        detail_lines = [f"作品《{work_title}》"] + messages
        if reason:
            detail_lines.append(f"原因：{reason}")
        _record_admin_action(request.user.user_id, ADMIN_ACTION_TARGET_WORK, work_id, 'update_work_moderation', '\n'.join(detail_lines), request=request)

    return Response({'success': True, 'message': '操作成功', 'updates': messages})


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def admin_update_chapter_status(request, chapter_id):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data or {}
    try:
        status_value = int(data.get('status'))
    except (TypeError, ValueError):
        return Response({'success': False, 'error': '章节状态值无效'}, status=status.HTTP_400_BAD_REQUEST)

    if status_value not in (0, 1, 2):
        return Response({'success': False, 'error': '章节状态值仅支持0/1/2'}, status=status.HTTP_400_BAD_REQUEST)

    reason = (data.get('reason') or '').strip()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ch.chapter_id, ch.work_id, ch.title, ch.status,
                   w.author_id, w.title AS work_title
            FROM chapters ch
            JOIN works w ON ch.work_id = w.work_id
            WHERE ch.chapter_id = %s
            """,
            [chapter_id]
        )
        chapter_row = cursor.fetchone()
        if not chapter_row:
            return Response({'success': False, 'error': '章节不存在'}, status=status.HTTP_404_NOT_FOUND)

        _, work_id, chapter_title, current_status, author_id, work_title = chapter_row

        if status_value == current_status:
            return Response({'success': True, 'message': '章节状态未发生变化'})

        cursor.execute(
            "UPDATE chapters SET status = %s, update_time = NOW() WHERE chapter_id = %s",
            [status_value, chapter_id]
        )

    status_text_map = {0: '草稿', 1: '已发布', 2: '已下架'}
    message_lines = [f"章节《{chapter_title}》的状态已调整为 {status_text_map.get(status_value, status_value)}。"]
    if reason:
        message_lines.append(f"原因：{reason}")
    _send_admin_message(author_id, ADMIN_MESSAGE_TYPE_CHAPTER, '\n'.join(message_lines), related_type=3, related_id=chapter_id)

    detail_lines = [f"章节《{chapter_title}》状态调整为 {status_text_map.get(status_value, status_value)}"]
    if reason:
        detail_lines.append(f"原因：{reason}")
    _record_admin_action(request.user.user_id, ADMIN_ACTION_TARGET_CHAPTER, chapter_id, 'update_chapter_status', '\n'.join(detail_lines), request=request)

    return Response({'success': True, 'message': '章节状态已更新'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_comments(request):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    search = (request.GET.get('search') or '').strip()
    status_filter = request.GET.get('status')
    page = max(1, int(request.GET.get('page', 1) or 1))
    page_size = int(request.GET.get('page_size', 20) or 20)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    conditions = ['1=1']
    params = []

    if search:
        like_value = f"%{search}%"
        conditions.append("(c.content LIKE %s OR w.title LIKE %s OR COALESCE(r.nickname, u.username, '') LIKE %s)")
        params.extend([like_value, like_value, like_value])

    if status_filter not in (None, '', 'all'):
        try:
            status_value = int(status_filter)
            conditions.append('c.status = %s')
            params.append(status_value)
        except (TypeError, ValueError):
            pass

    where_clause = ' AND '.join(conditions)

    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM comments c JOIN works w ON c.work_id = w.work_id WHERE {where_clause}",
            params
        )
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        cursor.execute(
            f"""
            SELECT c.comment_id, c.content, c.status, c.create_time,
                   c.reader_id, c.work_id, c.chapter_id,
                   COALESCE(r.nickname, u.username, '') AS reader_name,
                   w.title AS work_title
            FROM comments c
            JOIN works w ON c.work_id = w.work_id
            LEFT JOIN readers r ON c.reader_id = r.reader_id
            LEFT JOIN users u ON c.reader_id = u.user_id
            WHERE {where_clause}
            ORDER BY c.create_time DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset]
        )

        comments = []
        for row in cursor.fetchall():
            comments.append({
                'comment_id': row[0],
                'content': row[1],
                'status': row[2],
                'create_time': row[3].isoformat() if row[3] else None,
                'reader_id': row[4],
                'work_id': row[5],
                'chapter_id': row[6],
                'reader_name': row[7],
                'work_title': row[8]
            })

    return Response({'success': True, 'comments': comments, 'total': total})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_comment(request, comment_id):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    reason = (request.data.get('reason') if hasattr(request, 'data') else None) or ''

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.comment_id, c.reader_id, c.work_id, c.chapter_id, c.status,
                   c.content, w.title AS work_title
            FROM comments c
            JOIN works w ON c.work_id = w.work_id
            WHERE c.comment_id = %s
            """,
            [comment_id]
        )
        comment_row = cursor.fetchone()
        if not comment_row:
            return Response({'success': False, 'error': '评论不存在'}, status=status.HTTP_404_NOT_FOUND)

        _, reader_id, work_id, chapter_id, current_status, content, work_title = comment_row

        if current_status == 0:
            return Response({'success': True, 'message': '评论已处于删除状态'})

        cursor.execute("UPDATE comments SET status = 0 WHERE comment_id = %s", [comment_id])

    comment_text = content or ''
    excerpt = comment_text[:60]
    if len(comment_text) > 60:
        excerpt += '...'
    message_lines = [f"您在《{work_title}》下的评论已被管理员删除。", f"内容：{excerpt}"]
    if reason:
        message_lines.append(f"原因：{reason}")
    _send_admin_message(reader_id, ADMIN_MESSAGE_TYPE_COMMENT, '\n'.join(message_lines), related_type=4, related_id=comment_id)

    detail_lines = [f"评论ID {comment_id} 已删除", f"所属作品：《{work_title}》"]
    detail_lines.append(f"内容摘要：{excerpt}")
    if reason:
        detail_lines.append(f"原因：{reason}")
    _record_admin_action(request.user.user_id, ADMIN_ACTION_TARGET_COMMENT, comment_id, 'delete_comment', '\n'.join(detail_lines), request=request)

    return Response({'success': True, 'message': '评论已删除'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_action_logs(request):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    page = max(int(request.GET.get('page', 1) or 1), 1)
    page_size = max(1, min(int(request.GET.get('page_size', 20) or 20), 100))
    offset = (page - 1) * page_size

    admin_id = request.GET.get('admin_id')
    target_type = request.GET.get('target_type')
    action = request.GET.get('action')
    keyword = request.GET.get('keyword')
    start_time = _parse_time_param(request.GET.get('start_time'))
    end_time = _parse_time_param(request.GET.get('end_time'))

    conditions = []
    params = []

    if admin_id:
        try:
            admin_value = int(admin_id)
            conditions.append('admin_id = %s')
            params.append(admin_value)
        except (TypeError, ValueError):
            pass

    if target_type not in (None, '', 'all'):
        try:
            target_value = int(target_type)
            conditions.append('target_type = %s')
            params.append(target_value)
        except (TypeError, ValueError):
            pass

    if action:
        conditions.append('action = %s')
        params.append(action)

    if keyword:
        like_value = f"%{keyword}%"
        conditions.append('(detail LIKE %s OR extra_data LIKE %s)')
        params.extend([like_value, like_value])

    if start_time:
        conditions.append('create_time >= %s')
        params.append(start_time)

    if end_time:
        conditions.append('create_time <= %s')
        params.append(end_time)

    where_clause = ' AND '.join(conditions) if conditions else '1=1'

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM admin_action_logs WHERE {where_clause}", params)
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        query_params = list(params)
        query_params.extend([page_size, offset])

        cursor.execute(
            f"""
            SELECT log_id, admin_id, target_type, target_id, action, detail,
                   extra_data, ip_address, user_agent, create_time
            FROM admin_action_logs
            WHERE {where_clause}
            ORDER BY create_time DESC
            LIMIT %s OFFSET %s
            """,
            query_params
        )

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'log_id': row[0],
                'admin_id': row[1],
                'target_type': row[2],
                'target_id': row[3],
                'action': row[4],
                'detail': row[5],
                'extra': _safe_load_json(row[6]),
                'ip_address': row[7],
                'user_agent': row[8],
                'create_time': row[9].isoformat() if row[9] else None
            })

    return Response({'success': True, 'logs': logs, 'total': total})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_user_action_logs(request):
    if not _is_admin(request.user):
        return Response({'success': False, 'error': '需要管理员权限'}, status=status.HTTP_403_FORBIDDEN)

    page = max(int(request.GET.get('page', 1) or 1), 1)
    page_size = max(1, min(int(request.GET.get('page_size', 20) or 20), 100))
    offset = (page - 1) * page_size

    user_id = request.GET.get('user_id')
    target_type = request.GET.get('target_type')
    action = request.GET.get('action')
    keyword = request.GET.get('keyword')
    start_time = _parse_time_param(request.GET.get('start_time'))
    end_time = _parse_time_param(request.GET.get('end_time'))

    conditions = []
    params = []

    if user_id:
        try:
            user_value = int(user_id)
            conditions.append('user_id = %s')
            params.append(user_value)
        except (TypeError, ValueError):
            pass

    if target_type not in (None, '', 'all'):
        try:
            target_value = int(target_type)
            conditions.append('target_type = %s')
            params.append(target_value)
        except (TypeError, ValueError):
            pass

    if action:
        conditions.append('action = %s')
        params.append(action)

    if keyword:
        like_value = f"%{keyword}%"
        conditions.append('(detail LIKE %s OR extra_data LIKE %s)')
        params.extend([like_value, like_value])

    if start_time:
        conditions.append('create_time >= %s')
        params.append(start_time)

    if end_time:
        conditions.append('create_time <= %s')
        params.append(end_time)

    where_clause = ' AND '.join(conditions) if conditions else '1=1'

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM user_action_logs WHERE {where_clause}", params)
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        query_params = list(params)
        query_params.extend([page_size, offset])

        cursor.execute(
            f"""
            SELECT log_id, user_id, action, target_type, target_id, detail,
                   extra_data, ip_address, user_agent, create_time
            FROM user_action_logs
            WHERE {where_clause}
            ORDER BY create_time DESC
            LIMIT %s OFFSET %s
            """,
            query_params
        )

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'log_id': row[0],
                'user_id': row[1],
                'action': row[2],
                'target_type': row[3],
                'target_id': row[4],
                'detail': row[5],
                'extra': _safe_load_json(row[6]),
                'ip_address': row[7],
                'user_agent': row[8],
                'create_time': row[9].isoformat() if row[9] else None
            })

    return Response({'success': True, 'logs': logs, 'total': total})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    try:
        user_id = request.user.user_id

        if request.method == 'GET':
            profile = _fetch_user_profile(user_id)
            if not profile:
                return Response({'success': False, 'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'success': True, 'profile': profile})

        data = request.data
        nickname = data.get('nickname')
        avatar_url = data.get('avatar_url')
        intro = data.get('intro')

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM readers WHERE reader_id = %s", [user_id])
            reader_exists = cursor.fetchone() is not None

            if reader_exists:
                reader_updates = []
                params = []
                if nickname is not None:
                    reader_updates.append("nickname = %s")
                    params.append(nickname)
                if avatar_url is not None:
                    reader_updates.append("avatar_url = %s")
                    params.append(avatar_url)
                if reader_updates:
                    params.append(user_id)
                    cursor.execute(
                        f"UPDATE readers SET {', '.join(reader_updates)} WHERE reader_id = %s",
                        params
                    )
            elif nickname is not None or avatar_url is not None:
                cursor.execute(
                    """
                    INSERT INTO readers (reader_id, nickname, avatar_url, balance)
                    VALUES (%s, %s, %s, 0)
                    """,
                    [user_id, nickname or request.user.username, avatar_url or '']
                )

            author_updates = []
            params = []
            if nickname is not None:
                author_updates.append("pen_name = %s")
                params.append(nickname)
            if intro is not None:
                author_updates.append("intro = %s")
                params.append(intro)
            if author_updates:
                params.append(user_id)
                cursor.execute(
                    f"UPDATE authors SET {', '.join(author_updates)} WHERE author_id = %s",
                    params
                )

        profile = _fetch_user_profile(user_id)
        return Response({'success': True, 'profile': profile})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    try:
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'success': False, 'error': '请选择要上传的文件'}, status=status.HTTP_400_BAD_REQUEST)

        file_url = _save_uploaded_image(file_obj, 'avatars', MAX_AVATAR_FILE_SIZE)
        absolute_url = request.build_absolute_uri(file_url)

        return Response({'success': True, 'url': absolute_url, 'relative_url': file_url})

    except ValueError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({'success': False, 'error': '上传失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_cover(request):
    try:
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'success': False, 'error': '请选择要上传的文件'}, status=status.HTTP_400_BAD_REQUEST)

        file_url = _save_uploaded_image(file_obj, 'covers', MAX_COVER_FILE_SIZE)
        absolute_url = request.build_absolute_uri(file_url)

        return Response({'success': True, 'url': absolute_url, 'relative_url': file_url})

    except ValueError as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({'success': False, 'error': '上传失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_search_history(request):
    try:
        limit = request.GET.get('limit', 20)
        history = _fetch_user_search_history(request.user.user_id, limit)
        return Response({'success': True, 'history': history})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    try:
        user_id = request.user.user_id

        category_scores, tag_scores, tag_display_map, has_personal_signal = _get_user_preference_scores(user_id)
        popular_categories = _get_top_categories_by_popularity(limit=3)

        top_categories = _get_top_keys(category_scores, limit=3) if has_personal_signal else []
        top_tag_keys = _get_top_keys(tag_scores, limit=5) if has_personal_signal else []

        favorite_type_works = []
        used_ids = set()

        if has_personal_signal:
            favorite_type_works = _build_favorite_type_recommendations(
                category_scores,
                tag_scores,
                top_categories,
                top_tag_keys,
                limit=9
            )
            if not favorite_type_works:
                fallback_categories = top_categories or popular_categories or None
                favorite_type_works = _fetch_candidate_works(fallback_categories, limit=9)
            if not favorite_type_works:
                favorite_type_works = _fetch_candidate_works(None, limit=9)
            used_ids.update({work['work_id'] for work in favorite_type_works})

        search_fallback_categories = top_categories or popular_categories or None
        search_similar_works, has_search_history = _fetch_search_based_recommendations(
            user_id,
            search_fallback_categories,
            limit=8,
            exclude_ids=used_ids
        )
        if has_search_history:
            used_ids.update({work['work_id'] for work in search_similar_works})
        else:
            search_similar_works = []

        rank_categories = top_categories if top_categories else (popular_categories or [])
        favorite_rank_works = _build_favorite_rank_recommendations(rank_categories, limit_per_category=3, exclude_ids=used_ids)
        if not favorite_rank_works:
            fallback_categories = rank_categories or popular_categories or None
            favorite_rank_works = _fetch_candidate_works(fallback_categories, limit=9, exclude_ids=used_ids)
        if not favorite_rank_works:
            favorite_rank_works = _fetch_candidate_works(None, limit=9, exclude_ids=used_ids)

        category_name_map = _get_category_names(top_categories)
        rank_category_name_map = _get_category_names(rank_categories)
        top_tags = [tag_display_map.get(tag, tag) for tag in top_tag_keys] if has_personal_signal else []

        return Response({
            'success': True,
            'favorite_type_works': favorite_type_works,
            'search_similar_works': search_similar_works,
            'favorite_rank_works': favorite_rank_works,
            'meta': {
                'is_personalized': has_personal_signal,
                'has_search_history': has_search_history,
                'top_categories': [
                    {'category_id': cid, 'name': category_name_map.get(cid, '') or '未分类'}
                    for cid in top_categories
                ],
                'popular_categories': [
                    {'category_id': cid, 'name': rank_category_name_map.get(cid, '') or '未分类'}
                    for cid in rank_categories
                ],
                'top_tags': top_tags,
            }
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_recommendation_feedback(request):
    try:
        user_id = request.user.user_id
        data = request.data or {}

        work_id = data.get('work_id')
        if work_id in (None, ''):
            return Response({'success': False, 'error': '缺少作品ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            work_id = int(work_id)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': '作品ID无效'}, status=status.HTTP_400_BAD_REQUEST)

        raw_event = data.get('event') or data.get('event_type') or ''
        event_key = str(raw_event).strip().lower()

        event_type = FEEDBACK_EVENT_ALIASES.get(event_key)
        if event_type is None:
            try:
                event_type = int(raw_event)
            except (TypeError, ValueError):
                event_type = None

        if event_type not in FEEDBACK_EVENT_WEIGHTS:
            return Response({'success': False, 'error': '未知的反馈类型'}, status=status.HTTP_400_BAD_REQUEST)

        weight_value = data.get('weight', FEEDBACK_DEFAULT_WEIGHT)
        normalized_weight = _normalize_feedback_weight(weight_value)
        if normalized_weight <= 0:
            normalized_weight = FEEDBACK_DEFAULT_WEIGHT

        metadata = data.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata_candidate = json.loads(metadata)
                if isinstance(metadata_candidate, dict):
                    metadata = metadata_candidate
            except (json.JSONDecodeError, TypeError, ValueError):
                metadata = {'raw': metadata}

        extra_fields = {}
        for candidate_key in ('source', 'slot', 'section', 'position', 'query'):
            if candidate_key in data and data[candidate_key] not in (None, ''):
                extra_fields[candidate_key] = data[candidate_key]

        if isinstance(metadata, dict):
            extra_fields.update(metadata)
            metadata_payload = extra_fields
        else:
            metadata_payload = extra_fields or None

        _record_recommendation_feedback(
            user_id,
            work_id,
            event_type,
            weight_delta=normalized_weight,
            metadata=metadata_payload
        )

        return Response({'success': True})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_stats(request):
    try:
        user_id = request.user.user_id
        stats = _fetch_user_stats(user_id)
        return Response({'success': True, 'stats': stats})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_contact_info(request):
    try:
        user_id = request.user.user_id
        data = request.data

        phone = data.get('phone')
        email = data.get('email')

        if phone is None and email is None:
            return Response({'success': False, 'error': '未提供需要更新的联系方式'}, status=status.HTTP_400_BAD_REQUEST)

        phone_value = None
        if phone is not None:
            phone_value = phone.strip() if isinstance(phone, str) else phone
            if phone_value == '':
                phone_value = None
            elif not str(phone_value).isdigit() or len(str(phone_value)) < 6:
                return Response({'success': False, 'error': '手机号格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        email_value = None
        if email is not None:
            email_value = email.strip() if isinstance(email, str) else email
            if email_value == '':
                email_value = None
            elif '@' not in email_value:
                return Response({'success': False, 'error': '邮箱格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            if phone_value is not None:
                cursor.execute(
                    "SELECT user_id FROM users WHERE phone = %s AND user_id != %s",
                    [phone_value, user_id]
                )
                if cursor.fetchone():
                    return Response({'success': False, 'error': '该手机号已被其他账号绑定'}, status=status.HTTP_400_BAD_REQUEST)

            if email_value is not None:
                cursor.execute(
                    "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
                    [email_value, user_id]
                )
                if cursor.fetchone():
                    return Response({'success': False, 'error': '该邮箱已被其他账号绑定'}, status=status.HTTP_400_BAD_REQUEST)

            updates = []
            params = []
            if phone is not None:
                updates.append("phone = %s")
                params.append(phone_value)
            if email is not None:
                updates.append("email = %s")
                params.append(email_value)

            if updates:
                params.append(user_id)
                cursor.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s",
                    params
                )

        profile = _fetch_user_profile(user_id)
        return Response({'success': True, 'profile': profile})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_user_password(request):
    try:
        user_id = request.user.user_id
        data = request.data

        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not old_password or not new_password:
            return Response({'success': False, 'error': '请输入完整的密码信息'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'success': False, 'error': '新密码长度不能少于6位'}, status=status.HTTP_400_BAD_REQUEST)

        hashed_old = hash_password(old_password)
        hashed_new = hash_password(new_password)

        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE user_id = %s", [user_id])
            user_row = cursor.fetchone()

            if not user_row:
                return Response({'success': False, 'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

            if user_row[0] != hashed_old:
                return Response({'success': False, 'error': '当前密码不正确'}, status=status.HTTP_400_BAD_REQUEST)

            cursor.execute(
                "UPDATE users SET password = %s WHERE user_id = %s",
                [hashed_new, user_id]
            )

        return Response({'success': True, 'message': '密码更新成功'})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recharge_user_balance(request):
    try:
        user_id = request.user.user_id
        data = request.data
        amount = data.get('amount')

        if amount is None:
            return Response({'success': False, 'error': '充值金额不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount_value = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return Response({'success': False, 'error': '充值金额格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        if amount_value <= 0:
            return Response({'success': False, 'error': '充值金额必须大于0'}, status=status.HTTP_400_BAD_REQUEST)

        _ensure_point_transactions_table()

        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION")
            try:
                cursor.execute("SELECT 1 FROM readers WHERE reader_id = %s FOR UPDATE", [user_id])
                reader_exists = cursor.fetchone() is not None

                if not reader_exists:
                    cursor.execute(
                        """
                        INSERT INTO readers (reader_id, nickname, avatar_url, balance)
                        VALUES (%s, %s, '', 0)
                        """,
                        [user_id, request.user.username]
                    )

                cursor.execute(
                    "UPDATE readers SET balance = COALESCE(balance, 0) + %s WHERE reader_id = %s",
                    [amount_value, user_id]
                )

                cursor.execute(
                    """
                    INSERT INTO point_transactions (user_id, transaction_type, amount, description, create_time)
                    VALUES (%s, 'recharge', %s, %s, NOW())
                    """,
                    [user_id, amount_value, f'充值{amount_value}点券']
                )

                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise

            cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
            balance_row = cursor.fetchone()

        balance_value = float(balance_row[0]) if balance_row and balance_row[0] is not None else 0.0

        return Response({'success': True, 'balance': balance_value})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 作品管理API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_works(request):
    try:
        category_id = request.GET.get('category_id')
        status_filter = request.GET.get('status')
        sort_by = request.GET.get('sort_by', 'create_time')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        offset = (page - 1) * page_size
        
        with connection.cursor() as cursor:
            where_conditions = ["w.status IN (1, 2)"]
            params = []
            
            if category_id:
                where_conditions.append("w.category_id = %s")
                params.append(category_id)
            
            if status_filter in ("1", "2"):
                where_conditions.append("w.status = %s")
                params.append(int(status_filter))
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            order_mapping = {
                'create_time': 'w.create_time DESC',
                'update_time': 'w.update_time DESC',
                'read_count': 'w.read_count DESC',
                'collect_count': 'w.collect_count DESC'
            }
            order_clause = order_mapping.get(sort_by, 'w.create_time DESC')

            filter_params = params.copy()

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM works w
                WHERE {where_clause}
                """,
                filter_params
            )
            total_count_row = cursor.fetchone()
            total_count = int(total_count_row[0]) if total_count_row else 0

            cursor.execute(
                f"""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.status, w.create_time,
                       a.pen_name, c.name as category_name,
                       COALESCE(w.read_count, 0) AS read_count,
                       COALESCE(w.collect_count, 0) AS collect_count,
                       COALESCE(w.vote_count, 0) AS vote_count
                FROM works w
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN categories c ON w.category_id = c.category_id
                WHERE {where_clause}
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
                """,
                params + [page_size, offset]
            )
            
            works = []
            for row in cursor.fetchall():
                works.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'intro': row[3],
                    'status': row[4],
                    'create_time': row[5].isoformat() if row[5] else None,
                    'author_name': row[6],
                    'category_name': row[7],
                    'read_count': int(row[8] or 0),
                    'collect_count': int(row[9] or 0),
                    'vote_count': int(row[10] or 0)
                })
            
            return Response({'success': True, 'works': works, 'total': total_count})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_work(request):
    try:
        data = request.data
        user_id = request.user.user_id  # 从JWT认证中获取user_id
        
        if not _user_permission_allowed(user_id, 'can_publish'):
            return Response({'success': False, 'error': '您的账号已被限制发表作品，请联系管理员'}, status=status.HTTP_403_FORBIDDEN)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO works (author_id, category_id, title, cover_url, intro, tags, status, is_signed, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, 0, 0, NOW(), NOW())
            """, [
                user_id,
                data.get('category_id'),
                data.get('title'),
                data.get('cover_url', ''),
                data.get('intro', ''),
                json.dumps(data.get('tags', [])),
            ])
            
            work_id = cursor.lastrowid
            detail = f"创建作品《{data.get('title') or ''}》"
            _record_user_action(
                user_id,
                'create_work',
                USER_ACTION_TARGET_WORK,
                work_id,
                detail=detail,
                request=request,
                extra={
                    'title': data.get('title'),
                    'category_id': data.get('category_id'),
                    'tags': data.get('tags', [])
                }
            )
            return Response({'success': True, 'work_id': work_id})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 作品相关API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_works(request):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 获取当前用户的作品
            cursor.execute("""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.status,
                       w.read_count, w.collect_count, w.vote_count,
                       c.name as category_name, w.create_time, w.update_time,
                       COALESCE((SELECT SUM(amount) FROM subscriptions s WHERE s.work_id = w.work_id), 0) AS subscription_income,
                       COALESCE((SELECT COUNT(DISTINCT reader_id) FROM subscriptions s WHERE s.work_id = w.work_id), 0) AS subscription_count,
                       COALESCE((
                           SELECT COUNT(DISTINCT rr.reader_id)
                           FROM reading_records rr
                           JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                           WHERE ch.work_id = w.work_id
                       ), 0) AS unique_readers
                FROM works w
                LEFT JOIN categories c ON w.category_id = c.category_id
                WHERE w.author_id = %s
                ORDER BY w.update_time DESC
            """, [user_id])
            
            works = []
            summary = {
                'total_read_count': 0,
                'total_collect_count': 0,
                'total_vote_count': 0,
                'total_subscription_count': 0,
                'total_subscription_income': 0.0,
                'total_income': 0.0,
                'total_unique_readers': 0
            }

            for row in cursor.fetchall():
                subscription_income_value = float(row[11]) if row[11] is not None else 0.0
                subscription_count_value = int(row[12]) if row[12] is not None else 0
                unique_readers_value = int(row[13]) if row[13] is not None else 0

                work_data = {
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'intro': row[3],
                    'status': row[4],
                    'read_count': row[5] or 0,
                    'collect_count': row[6] or 0,
                    'vote_count': row[7] or 0,
                    'category_name': row[8],
                    'create_time': row[9].isoformat() if row[9] else None,
                    'update_time': row[10].isoformat() if row[10] else None,
                    'subscription_income': subscription_income_value,
                    'subscription_count': subscription_count_value,
                    'unique_readers': unique_readers_value
                }

                summary['total_read_count'] += work_data['read_count']
                summary['total_collect_count'] += work_data['collect_count']
                summary['total_vote_count'] += work_data['vote_count']
                summary['total_subscription_count'] += subscription_count_value
                summary['total_subscription_income'] += subscription_income_value
                summary['total_income'] += subscription_income_value
                summary['total_unique_readers'] += unique_readers_value

                works.append(work_data)

        return Response({'success': True, 'works': works, 'summary': summary})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work_detail(request, work_id):
    try:
        user_id = getattr(request.user, 'user_id', None)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.tags, w.status,
                       w.category_id, w.read_count, w.collect_count, w.vote_count,
                       w.create_time, w.update_time, c.name AS category_name,
                       w.author_id, a.pen_name, a.intro AS author_intro,
                       r.nickname AS reader_nickname, r.avatar_url AS reader_avatar,
                       u.username AS author_username
                FROM works w
                LEFT JOIN categories c ON w.category_id = c.category_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN readers r ON w.author_id = r.reader_id
                LEFT JOIN users u ON w.author_id = u.user_id
                WHERE w.work_id = %s
            """, [work_id])

            work_data = cursor.fetchone()
            if not work_data:
                return Response({'success': False, 'error': '作品不存在'},
                                status=status.HTTP_404_NOT_FOUND)

            author_id = work_data[13]
            is_author = user_id == author_id
            pen_name = (work_data[14] or '').strip()
            author_intro = work_data[15] or ''
            reader_nickname = (work_data[16] or '').strip()
            reader_avatar_url = work_data[17] or ''
            username = (work_data[18] or '').strip()

            author_name = pen_name or reader_nickname or username
            if not author_name and author_id:
                cursor.execute("""
                    SELECT COALESCE(a.pen_name, r.nickname, u.username)
                    FROM authors a
                    LEFT JOIN readers r ON a.author_id = r.reader_id
                    LEFT JOIN users u ON a.author_id = u.user_id
                    WHERE a.author_id = %s
                """, [author_id])
                author_row = cursor.fetchone()
                if author_row and author_row[0]:
                    author_name = author_row[0]

            category_name = work_data[12] or ''
            category_id = work_data[6]
            if not category_name and category_id:
                cursor.execute("SELECT name FROM categories WHERE category_id = %s", [category_id])
                category_row = cursor.fetchone()
                if category_row and category_row[0]:
                    category_name = category_row[0]
            if not category_name:
                category_name = '未分类'

            intro_value = work_data[3] or ''
            tags_value = []
            if work_data[4]:
                try:
                    tags_value = json.loads(work_data[4])
                    if not isinstance(tags_value, list):
                        tags_value = []
                except (ValueError, TypeError, json.JSONDecodeError):
                    tags_value = []

            work = {
                'work_id': work_data[0],
                'title': work_data[1],
                'cover_url': work_data[2],
                'intro': intro_value.replace('\r\n', '\n'),
                'tags': tags_value,
                'status': work_data[5],
                'category_id': category_id,
                'read_count': int(work_data[7] or 0),
                'collect_count': int(work_data[8] or 0),
                'vote_count': int(work_data[9] or 0),
                'create_time': work_data[10].isoformat() if work_data[10] else None,
                'update_time': work_data[11].isoformat() if work_data[11] else None,
                'category_name': category_name,
                'author_id': author_id,
                'author_name': author_name,
                'author_pen_name': pen_name,
                'author_nickname': reader_nickname,
                'author_username': username,
                'author_avatar_url': reader_avatar_url
            }

            cursor.execute("""
                SELECT COUNT(*)
                FROM reading_records rr
                JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                WHERE ch.work_id = %s
            """, [work_id])
            read_count_row = cursor.fetchone()
            aggregated_read_count = int(read_count_row[0]) if read_count_row and read_count_row[0] is not None else 0
            work['read_count'] = max(work['read_count'], aggregated_read_count)

            cursor.execute("SELECT COUNT(*) FROM collections WHERE work_id = %s", [work_id])
            collect_row = cursor.fetchone()
            aggregated_collect_count = int(collect_row[0]) if collect_row and collect_row[0] is not None else 0
            work['collect_count'] = max(work['collect_count'], aggregated_collect_count)

            cursor.execute("""
                SELECT COUNT(DISTINCT reader_id), COALESCE(SUM(amount), 0)
                FROM subscriptions
                WHERE work_id = %s
            """, [work_id])
            subscription_row = cursor.fetchone()
            work['subscription_count'] = int(subscription_row[0]) if subscription_row and subscription_row[0] is not None else 0
            work['subscription_income'] = float(subscription_row[1]) if subscription_row and subscription_row[1] is not None else 0.0

            cursor.execute("SELECT COALESCE(SUM(count), 0) FROM votes WHERE work_id = %s", [work_id])
            vote_row = cursor.fetchone()
            aggregated_vote_count = int(vote_row[0]) if vote_row and vote_row[0] is not None else 0
            work['vote_count'] = max(work['vote_count'], aggregated_vote_count)

            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_count,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS published_count
                FROM chapters
                WHERE work_id = %s
            """, [work_id])
            chapter_counts = cursor.fetchone()
            total_count = chapter_counts[0] if chapter_counts and chapter_counts[0] else 0
            published_count = chapter_counts[1] if chapter_counts and chapter_counts[1] else 0

            work['chapter_count'] = total_count
            work['published_chapter_count'] = published_count

            cursor.execute("""
                SELECT COUNT(DISTINCT rr.reader_id)
                FROM reading_records rr
                JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                WHERE ch.work_id = %s
            """, [work_id])
            unique_reader_row = cursor.fetchone()
            work['unique_readers'] = int(unique_reader_row[0]) if unique_reader_row and unique_reader_row[0] is not None else 0

            is_collected = False
            if user_id:
                cursor.execute("""
                    SELECT 1 FROM collections 
                    WHERE reader_id = %s AND work_id = %s
                """, [user_id, work_id])
                is_collected = cursor.fetchone() is not None

            cursor.execute("""
                SELECT COUNT(*), 
                       COALESCE(SUM(read_count), 0),
                       COALESCE(SUM(collect_count), 0),
                       COALESCE(SUM(vote_count), 0)
                FROM works
                WHERE author_id = %s
            """, [author_id])
            author_stats = cursor.fetchone()

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM subscriptions WHERE work_id IN (SELECT work_id FROM works WHERE author_id = %s)",
                [author_id]
            )
            author_income_row = cursor.fetchone()
            author_subscription_income = float(author_income_row[0]) if author_income_row and author_income_row[0] is not None else 0.0

            cursor.execute("SELECT COALESCE(total_income, 0) FROM authors WHERE author_id = %s", [author_id])
            author_total_income_row = cursor.fetchone()
            author_total_income = float(author_total_income_row[0]) if author_total_income_row and author_total_income_row[0] is not None else 0.0

            cursor.execute("""
                SELECT COUNT(DISTINCT reader_id)
                FROM collections
                WHERE work_id IN (
                    SELECT work_id FROM works WHERE author_id = %s
                )
            """, [author_id])
            fans_result = cursor.fetchone()
            fans_count = fans_result[0] if fans_result and fans_result[0] else 0

            author_info = {
                'author_id': author_id,
                'author_name': author_name,
                'pen_name': pen_name or author_name,
                'nickname': reader_nickname,
                'username': username,
                'avatar_url': reader_avatar_url,
                'intro': author_intro,
                'works_count': author_stats[0] if author_stats else 0,
                'total_reads': author_stats[1] if author_stats else 0,
                'total_collects': author_stats[2] if author_stats else 0,
                'total_votes': author_stats[3] if author_stats else 0,
                'fans_count': fans_count,
                'subscription_income': author_subscription_income,
                'total_income': author_total_income
            }

            cursor.execute("""
                SELECT work_id, title, cover_url
                FROM works
                WHERE author_id = %s AND work_id <> %s AND status IN (0, 1, 2)
                ORDER BY update_time DESC
                LIMIT 6
            """, [author_id, work_id])

            author_works = []
            for row in cursor.fetchall():
                author_works.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2]
                })

            cursor.execute("""
                SELECT v.vote_id, r.nickname AS reader_name, v.count, v.message, v.vote_time
                FROM votes v
                LEFT JOIN readers r ON v.reader_id = r.reader_id
                WHERE v.work_id = %s
                ORDER BY v.vote_time DESC
                LIMIT 20
            """, [work_id])

            vote_records = []
            for row in cursor.fetchall():
                vote_records.append({
                    'vote_id': row[0],
                    'reader_name': row[1] or '匿名读者',
                    'count': row[2],
                    'message': row[3],
                    'vote_time': row[4].isoformat() if row[4] else None
                })

            if user_id:
                detail = f"查看作品《{work.get('title', '')}》详情"
                _record_user_action(
                    user_id,
                    'view_work_detail',
                    USER_ACTION_TARGET_WORK,
                    work_id,
                    detail=detail,
                    request=request,
                    extra={'is_author': is_author}
                )

                if not is_author:
                    metadata_payload = {}
                    source_param = request.GET.get('source') or request.GET.get('from')
                    if source_param:
                        metadata_payload['source'] = source_param
                    slot_param = request.GET.get('slot') or request.GET.get('section')
                    if slot_param:
                        metadata_payload['slot'] = slot_param
                    if is_collected:
                        metadata_payload['is_collected'] = True

                    _record_recommendation_feedback(
                        user_id,
                        work_id,
                        FEEDBACK_EVENT_VIEW,
                        weight_delta=1.0,
                        metadata=metadata_payload or None
                    )

            return Response({
                'success': True,
                'work': work,
                'is_author': is_author,
                'is_collected': is_collected,
                'author_info': author_info,
                'author_works': author_works,
                'vote_records': vote_records
            })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work_metrics(request, work_id):
    try:
        user_id = request.user.user_id

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT title, author_id
                FROM works
                WHERE work_id = %s
            """, [work_id])

            work_row = cursor.fetchone()
            if not work_row:
                return Response({'success': False, 'error': '作品不存在'}, status=status.HTTP_404_NOT_FOUND)

            work_title, author_id = work_row

            if author_id != user_id:
                return Response({'success': False, 'error': '无权查看该作品数据'}, status=status.HTTP_403_FORBIDDEN)

            cursor.execute("""
                SELECT COUNT(*) AS total_reads,
                       COUNT(DISTINCT rr.reader_id) AS unique_readers
                FROM reading_records rr
                JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                WHERE ch.work_id = %s
            """, [work_id])
            reading_row = cursor.fetchone()
            total_reads = int(reading_row[0]) if reading_row and reading_row[0] is not None else 0
            unique_readers = int(reading_row[1]) if reading_row and reading_row[1] is not None else 0

            cursor.execute("""
                SELECT COUNT(*)
                FROM collections
                WHERE work_id = %s
            """, [work_id])
            collect_row = cursor.fetchone()
            collect_count = int(collect_row[0]) if collect_row and collect_row[0] is not None else 0

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0),
                       COUNT(DISTINCT reader_id)
                FROM subscriptions
                WHERE work_id = %s
            """, [work_id])
            subscription_row = cursor.fetchone()
            subscription_income = float(subscription_row[0]) if subscription_row and subscription_row[0] is not None else 0.0
            subscription_count = int(subscription_row[1]) if subscription_row and subscription_row[1] is not None else 0

            cursor.execute("""
                SELECT COALESCE(SUM(count), 0)
                FROM votes
                WHERE work_id = %s
            """, [work_id])
            vote_row = cursor.fetchone()
            vote_count = int(vote_row[0]) if vote_row and vote_row[0] is not None else 0

            metrics = {
                'work_id': work_id,
                'title': work_title,
                'total_reads': total_reads,
                'unique_readers': unique_readers,
                'collect_count': collect_count,
                'subscription_count': subscription_count,
                'subscription_income': subscription_income,
                'vote_count': vote_count
            }

            _record_user_action(
                user_id,
                'view_work_metrics',
                USER_ACTION_TARGET_WORK,
                work_id,
                detail=f"查看作品《{work_title}》数据概览",
                request=request
            )

            return Response({'success': True, 'metrics': metrics})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_work(request, work_id):
    try:
        data = request.data
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查作品是否存在且属于当前用户
            cursor.execute("""
                SELECT status FROM works 
                WHERE work_id = %s AND author_id = %s
            """, [work_id, user_id])

            row = cursor.fetchone()
            if not row:
                return Response({'success': False, 'error': '作品不存在或无权限'},
                                status=status.HTTP_404_NOT_FOUND)

            current_status = int(row[0]) if row[0] is not None else 0

            status_value = data.get('status', current_status)
            try:
                new_status = int(status_value)
            except (TypeError, ValueError):
                return Response({'success': False, 'error': '作品状态不合法'},
                                status=status.HTTP_400_BAD_REQUEST)

            if new_status not in (0, 1, 2, 3):
                return Response({'success': False, 'error': '作品状态不合法'},
                                status=status.HTTP_400_BAD_REQUEST)

            if current_status in (1, 2) and new_status == 0:
                return Response({'success': False, 'error': '已发布作品无法恢复为草稿状态'},
                                status=status.HTTP_400_BAD_REQUEST)

            # 更新作品信息
            cursor.execute("""
                UPDATE works 
                SET title = %s, category_id = %s, intro = %s, tags = %s, 
                    cover_url = %s, status = %s, update_time = NOW()
                WHERE work_id = %s
            """, [
                data.get('title'),
                data.get('category_id'),
                data.get('intro'),
                json.dumps(data.get('tags', [])),
                data.get('cover_url', ''),
                new_status,
                work_id
            ])
            
            detail = f"更新作品《{data.get('title') or ''}》"
            _record_user_action(
                user_id,
                'update_work',
                USER_ACTION_TARGET_WORK,
                work_id,
                detail=detail,
                request=request,
                extra={
                    'title': data.get('title'),
                    'category_id': data.get('category_id'),
                    'status': new_status,
                    'tags': data.get('tags', [])
                }
            )
            return Response({'success': True, 'message': '作品更新成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_categories(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT category_id, name, parent_id, sort_num
                FROM categories
                ORDER BY sort_num, name
            """)
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'category_id': row[0],
                    'name': row[1],
                    'parent_id': row[2],
                    'sort_num': row[3]
                })
            
            return Response({'success': True, 'categories': categories})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 章节管理API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chapters(request, work_id):
    try:
        user_id = request.user.user_id
 
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT title, author_id 
                FROM works 
                WHERE work_id = %s
            """, [work_id])
 
            work_data = cursor.fetchone()
            if not work_data:
                return Response({'success': False, 'error': '作品不存在'},
                                status=status.HTTP_404_NOT_FOUND)
 
            work_title, author_id = work_data
            is_author = (author_id == user_id)

            has_full_subscription = False
            subscribed_chapters = set()
            if not is_author:
                has_full_subscription, subscribed_chapters = _get_user_subscription_status(user_id, work_id)
 
            if is_author:
                cursor.execute("""
                    SELECT chapter_id, title, content, intro, word_count, is_free, status,
                           chapter_order, create_time, publish_time
                    FROM chapters 
                    WHERE work_id = %s 
                    ORDER BY chapter_order ASC, create_time ASC
                """, [work_id])
            else:
                cursor.execute("""
                    SELECT chapter_id, title, intro, word_count, is_free, status,
                           chapter_order, publish_time
                    FROM chapters 
                    WHERE work_id = %s AND status = 1
                    ORDER BY chapter_order ASC, publish_time ASC, chapter_id ASC
                """, [work_id])
 
            chapters = []
            for row in cursor.fetchall():
                if is_author:
                    chapter_word_count = row[4] or 0
                    cost = calculate_chapter_cost(chapter_word_count)
                    chapters.append({
                        'chapter_id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'intro': row[3],
                        'word_count': chapter_word_count,
                        'is_free': bool(row[5]),
                        'status': row[6],
                        'chapter_order': row[7],
                        'create_time': row[8].isoformat() if row[8] else None,
                        'publish_time': row[9].isoformat() if row[9] else None,
                        'cost': cost,
                        'is_subscribed': True
                    })
                else:
                    chapter_word_count = row[3] or 0
                    is_free = bool(row[4])
                    is_subscribed = has_full_subscription or row[0] in subscribed_chapters
                    cost = calculate_chapter_cost(chapter_word_count)
                    chapters.append({
                        'chapter_id': row[0],
                        'title': row[1],
                        'intro': row[2],
                        'word_count': chapter_word_count,
                        'is_free': is_free,
                        'status': row[5],
                        'chapter_order': row[6],
                        'publish_time': row[7].isoformat() if row[7] else None,
                        'cost': cost,
                        'is_subscribed': is_subscribed
                    })
 
            _record_user_action(
                user_id,
                'view_chapter_list',
                USER_ACTION_TARGET_WORK,
                work_id,
                detail=f"查看作品《{work_title}》章节列表",
                request=request,
                extra={'is_author': is_author}
            )

            return Response({
                'success': True,
                'chapters': chapters,
                'work_title': work_title,
                'is_author': is_author,
                'has_full_subscription': has_full_subscription,
                'subscribed_chapter_ids': list(subscribed_chapters)
            })
             
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chapter(request, work_id):
    try:
        data = request.data
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查作品是否属于当前用户
            cursor.execute("""
                SELECT work_id FROM works 
                WHERE work_id = %s AND author_id = %s
            """, [work_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '作品不存在或无权限'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            if not _user_permission_allowed(user_id, 'can_publish'):
                return Response({'success': False, 'error': '您的账号已被限制更新作品，请联系管理员'}, status=status.HTTP_403_FORBIDDEN)

            moderation = _get_work_moderation(work_id)
            if moderation.get('updates_blocked'):
                return Response({'success': False, 'error': '该作品已被管理员禁止更新'}, status=status.HTTP_403_FORBIDDEN)
            if moderation.get('chapters_blocked'):
                return Response({'success': False, 'error': '该作品章节已被管理员封禁'}, status=status.HTTP_403_FORBIDDEN)

            # 获取下一个章节序号
            cursor.execute("""
                SELECT COALESCE(MAX(chapter_order), 0) + 1 
                FROM chapters WHERE work_id = %s
            """, [work_id])
            next_order = cursor.fetchone()[0]
            
            content = data.get('content', '')
            word_count = _calculate_word_count(content)
            is_free = 1 if _to_bool(data.get('is_free'), True) else 0

            cursor.execute("""
                INSERT INTO chapters (work_id, title, content, intro, word_count, is_free,
                                    chapter_order, status, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW())
            """, [
                work_id,
                data.get('title'),
                content,
                data.get('intro', ''),
                word_count,
                is_free,
                next_order
            ])
 
            chapter_id = cursor.lastrowid
            detail = f"创建章节《{data.get('title') or ''}》"
            _record_user_action(
                user_id,
                'create_chapter',
                USER_ACTION_TARGET_CHAPTER,
                chapter_id,
                detail=detail,
                request=request,
                extra={
                    'work_id': work_id,
                    'is_free': bool(is_free),
                    'word_count': word_count
                }
            )
            return Response({'success': True, 'chapter_id': chapter_id})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def update_chapter(request, work_id, chapter_id):
    try:
        user_id = request.user.user_id
        update_recipient_ids = set()
        chapter_title_new = None
        chapter_published_now = False
 
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT title, author_id 
                FROM works 
                WHERE work_id = %s
            """, [work_id])

            work_row = cursor.fetchone()
            if not work_row:
                return Response({'success': False, 'error': '作品不存在'},
                                status=status.HTTP_404_NOT_FOUND)

            work_title, author_id = work_row
            is_author = (author_id == user_id)
 
            cursor.execute("""
                SELECT chapter_id, title, content, intro, word_count, is_free, status,
                       chapter_order, create_time, publish_time
                FROM chapters
                WHERE chapter_id = %s AND work_id = %s
            """, [chapter_id, work_id])
 
            chapter_row = cursor.fetchone()
            if not chapter_row:
                return Response({'success': False, 'error': '章节不存在'},
                                status=status.HTTP_404_NOT_FOUND)
 
            chapter_status = chapter_row[6]
            is_free = bool(chapter_row[5])
            word_count = chapter_row[4] or 0
            moderation = _get_work_moderation(work_id)
 
            if request.method == 'GET':
                if not is_author and chapter_status != 1:
                    return Response({'success': False, 'error': '章节不存在或未发布'},
                                    status=status.HTTP_404_NOT_FOUND)
 
                is_subscribed = False
                if not is_author and not is_free:
                    is_subscribed = _user_has_subscription(user_id, work_id, chapter_id)
 
                cost = calculate_chapter_cost(word_count)
                can_read = is_author or is_free or is_subscribed
 
                chapter = {
                    'chapter_id': chapter_row[0],
                    'title': chapter_row[1],
                    'content': chapter_row[2] if can_read else '',
                    'intro': chapter_row[3],
                    'word_count': word_count,
                    'is_free': is_free,
                    'status': chapter_status,
                    'chapter_order': chapter_row[7],
                    'create_time': chapter_row[8].isoformat() if chapter_row[8] else None,
                    'publish_time': chapter_row[9].isoformat() if chapter_row[9] else None
                }
 
                response_payload = {
                    'success': True,
                    'chapter': chapter,
                    'is_author': is_author,
                    'is_subscribed': is_author or is_subscribed,
                    'can_read': can_read,
                    'cost': cost
                }
 
                if not can_read and not is_free:
                    response_payload['message'] = '该章节为付费章节，请先订阅后再阅读'
                elif not is_author and can_read:
                    _record_chapter_reading(user_id, work_id, chapter_id)
 
                detail = f"查看章节《{chapter_row[1]}》详情"
                _record_user_action(
                    user_id,
                    'view_chapter_detail',
                    USER_ACTION_TARGET_CHAPTER,
                    chapter_id,
                    detail=detail,
                    request=request,
                    extra={
                        'work_id': work_id,
                        'can_read': can_read,
                        'is_author': is_author
                    }
                )

                return Response(response_payload)
 
            # PUT 请求权限与限制校验
            if not is_author:
                return Response({'success': False, 'error': '章节不存在或无权限'},
                                status=status.HTTP_403_FORBIDDEN)

            if not _user_permission_allowed(user_id, 'can_publish'):
                return Response({'success': False, 'error': '您的账号更新作品的权限已被暂停'},
                                status=status.HTTP_403_FORBIDDEN)

            if moderation.get('updates_blocked'):
                return Response({'success': False, 'error': '该作品已被管理员禁止更新'},
                                status=status.HTTP_403_FORBIDDEN)

            if moderation.get('chapters_blocked'):
                return Response({'success': False, 'error': '该作品章节已被管理员封禁'},
                                status=status.HTTP_403_FORBIDDEN)
 
            data = request.data
            new_status = data.get('status', chapter_status)
            try:
                new_status_int = int(new_status)
            except (TypeError, ValueError):
                new_status_int = chapter_status
            new_content = data.get('content')
            if new_content is None:
                new_content = chapter_row[2]
            new_word_count = _calculate_word_count(new_content)
            new_is_free = 1 if _to_bool(data.get('is_free'), is_free) else 0
            chapter_title_new = data.get('title', chapter_row[1])
 
            cursor.execute("""
                UPDATE chapters 
                SET title = %s, content = %s, intro = %s, word_count = %s,
                    is_free = %s, status = %s, update_time = NOW(),
                    publish_time = CASE WHEN %s = 1 THEN COALESCE(publish_time, NOW()) ELSE publish_time END
                WHERE chapter_id = %s AND work_id = %s
            """, [
                chapter_title_new,
                new_content,
                data.get('intro', chapter_row[3] or ''),
                new_word_count,
                new_is_free,
                new_status_int,
                new_status_int,
                chapter_id,
                work_id
            ])

            chapter_published_now = (chapter_status != 1 and new_status_int == 1)
            if chapter_published_now:
                cursor.execute(
                    "SELECT DISTINCT reader_id FROM collections WHERE work_id = %s",
                    [work_id]
                )
                for row in cursor.fetchall():
                    recipient_id = row[0]
                    if recipient_id and recipient_id not in (user_id, author_id):
                        update_recipient_ids.add(recipient_id)

                cursor.execute(
                    "SELECT DISTINCT reader_id FROM subscriptions WHERE work_id = %s",
                    [work_id]
                )
                for row in cursor.fetchall():
                    recipient_id = row[0]
                    if recipient_id and recipient_id not in (user_id, author_id):
                        update_recipient_ids.add(recipient_id)
 
        detail = f"更新章节《{chapter_title_new or chapter_row[1]}》"
        _record_user_action(
            user_id,
            'update_chapter',
            USER_ACTION_TARGET_CHAPTER,
            chapter_id,
            detail=detail,
            request=request,
            extra={
                'work_id': work_id,
                'status': new_status_int,
                'is_free': bool(new_is_free),
                'word_count': new_word_count
            }
        )

        if chapter_published_now and update_recipient_ids:
            work_title_display = work_title or f'作品{work_id}'
            chapter_title_display = chapter_title_new or chapter_row[1] or f'章节{chapter_id}'
            message_content = (
                f"您关注的作品《{work_title_display}》更新了新章节《{chapter_title_display}》，快去阅读吧！"
            )
            for recipient_id in update_recipient_ids:
                _create_message(
                    recipient_id=recipient_id,
                    message_type=MESSAGE_TYPE_WORK_UPDATE,
                    content=message_content,
                    related_type=3,
                    related_id=chapter_id,
                    sender_id=user_id
                )

        return Response({'success': True, 'message': '章节更新成功'})
 
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_chapter(request, work_id, chapter_id):
    try:
        user_id = request.user.user_id

        if not _user_permission_allowed(user_id, 'can_subscribe'):
            return Response({'success': False, 'error': '您的账号已被限制订阅付费内容'}, status=status.HTTP_403_FORBIDDEN)

        _ensure_point_transactions_table()
        _ensure_user_tickets_table()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.chapter_id, c.title, c.word_count, c.is_free, c.status,
                       w.author_id, w.title
                FROM chapters c
                JOIN works w ON c.work_id = w.work_id
                WHERE c.chapter_id = %s AND c.work_id = %s
            """, [chapter_id, work_id])

            chapter_row = cursor.fetchone()
            if not chapter_row:
                return Response({'success': False, 'error': '章节不存在'}, status=status.HTTP_404_NOT_FOUND)

            _, chapter_title, word_count, is_free, status_value, author_id, work_title = chapter_row
            is_free = bool(is_free)

            moderation = _get_work_moderation(work_id)
            if moderation.get('is_hidden'):
                return Response({'success': False, 'error': '作品已被管理员屏蔽，暂无法订阅'}, status=status.HTTP_403_FORBIDDEN)
            if moderation.get('subscriptions_blocked'):
                return Response({'success': False, 'error': '作品订阅功能已被管理员暂停'}, status=status.HTTP_403_FORBIDDEN)
            if moderation.get('chapters_blocked'):
                return Response({'success': False, 'error': '作品章节已被封禁，暂无法订阅'}, status=status.HTTP_403_FORBIDDEN)

            if status_value != 1:
                return Response({'success': False, 'error': '该章节尚未发布，暂无法订阅'},
                                status=status.HTTP_400_BAD_REQUEST)

            if author_id == user_id:
                return Response({'success': True, 'message': '作者无需订阅自己的章节', 'cost': 0})

            if is_free:
                return Response({'success': True, 'message': '该章节为免费章节，无需订阅', 'cost': 0})

            has_full_subscription, subscribed_chapters = _get_user_subscription_status(user_id, work_id)
            if has_full_subscription or chapter_id in subscribed_chapters:
                return Response({'success': True, 'message': '您已订阅该章节', 'cost': 0})

            cost = calculate_chapter_cost(word_count)
            cost_decimal = Decimal(str(cost))

            if cost <= 0:
                return Response({'success': True, 'message': '该章节无需扣除点券', 'cost': 0})

            cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
            reader_row = cursor.fetchone()
            if not reader_row:
                return Response({'success': False, 'error': '读者信息不存在'}, status=status.HTTP_404_NOT_FOUND)

            balance = reader_row[0] if reader_row[0] is not None else Decimal('0')
            if not isinstance(balance, Decimal):
                balance = Decimal(str(balance))

            if balance < cost_decimal:
                return Response({'success': False, 'error': '点券余额不足'}, status=status.HTTP_400_BAD_REQUEST)

            ticket_reward = 0
            cursor.execute("START TRANSACTION")
            try:
                cursor.execute(
                    "UPDATE readers SET balance = balance - %s WHERE reader_id = %s",
                    [cost_decimal, user_id]
                )

                cursor.execute(
                    """
                    INSERT INTO subscriptions (reader_id, work_id, chapter_id, sub_time, amount)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    [user_id, work_id, chapter_id, cost_decimal]
                )

                cursor.execute(
                    """
                    INSERT INTO point_transactions (user_id, transaction_type, amount, description, create_time)
                    VALUES (%s, 'subscription', -%s, %s, NOW())
                    """,
                    [user_id, cost_decimal, f'订阅章节 {chapter_id}']
                )

                cursor.execute(
                    "UPDATE authors SET total_income = COALESCE(total_income, 0) + %s WHERE author_id = %s",
                    [cost_decimal, author_id]
                )

                _ensure_user_ticket_wallet(cursor, user_id)
                cursor.execute(
                    "SELECT ticket_balance, progress FROM user_tickets WHERE user_id = %s FOR UPDATE",
                    [user_id]
                )
                ticket_row = cursor.fetchone()
                current_progress = Decimal('0')
                if ticket_row and ticket_row[1] is not None:
                    current_progress = Decimal(str(ticket_row[1]))

                total_for_reward = current_progress + cost_decimal
                reward_decimal, new_progress = divmod(total_for_reward, MONTHLY_TICKET_UNIT)
                ticket_reward = int(reward_decimal)
                new_progress = new_progress.quantize(Decimal('0.01'))

                if ticket_reward > 0:
                    cursor.execute(
                        """
                        UPDATE user_tickets
                        SET ticket_balance = ticket_balance + %s,
                            progress = %s,
                            total_earned = total_earned + %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        [ticket_reward, new_progress, ticket_reward, user_id]
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE user_tickets
                        SET progress = %s,
                            updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        [new_progress, user_id]
                    )

                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise

            cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
            new_balance_row = cursor.fetchone()
            new_balance = float(new_balance_row[0]) if new_balance_row and new_balance_row[0] is not None else 0.0
            cursor.execute("SELECT ticket_balance FROM user_tickets WHERE user_id = %s", [user_id])
            ticket_balance_row = cursor.fetchone()
            ticket_balance = int(ticket_balance_row[0]) if ticket_balance_row and ticket_balance_row[0] is not None else 0

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM subscriptions WHERE work_id = %s",
                [work_id]
            )
            work_income_row = cursor.fetchone()
            work_income = float(work_income_row[0]) if work_income_row and work_income_row[0] is not None else 0.0

            cursor.execute(
                "SELECT COALESCE(total_income, 0) FROM authors WHERE author_id = %s",
                [author_id]
            )
            author_income_row = cursor.fetchone()
            author_income = float(author_income_row[0]) if author_income_row and author_income_row[0] is not None else 0.0

            success_message = '订阅成功'
            if cost > 0:
                success_message += f'，消耗 {cost} 点券'
            if ticket_reward > 0:
                success_message += f'，获得 {ticket_reward} 张月票'

            detail = f"订阅章节 {chapter_id}"
            _record_user_action(
                user_id,
                'subscribe_chapter',
                USER_ACTION_TARGET_SUBSCRIPTION,
                chapter_id,
                detail=detail,
                request=request,
                extra={
                    'work_id': work_id,
                    'cost': cost,
                    'ticket_reward': ticket_reward
                }
            )

            _record_recommendation_feedback(
                user_id,
                work_id,
                FEEDBACK_EVENT_SUBSCRIBE,
                weight_delta=1.0,
                metadata={
                    'chapter_id': chapter_id,
                    'cost': cost,
                    'ticket_reward': ticket_reward
                }
            )

            if author_id and author_id != user_id:
                reader_name = _get_user_display_name(user_id) or f'用户{user_id}'
                contribution_text = f"，贡献 {cost} 点券" if cost > 0 else ''
                chapter_title_display = chapter_title or f'章节{chapter_id}'
                work_title_display = work_title or f'作品{work_id}'
                message_content = (
                    f"读者「{reader_name}」订阅了作品《{work_title_display}》的章节《{chapter_title_display}》{contribution_text}。"
                )
                _create_message(
                    recipient_id=author_id,
                    message_type=MESSAGE_TYPE_SUBSCRIPTION,
                    content=message_content,
                    related_type=3,
                    related_id=chapter_id,
                    sender_id=user_id
                )

            return Response({
                'success': True,
                'message': success_message,
                'cost': cost,
                'balance': new_balance,
                'ticket_rewarded': ticket_reward,
                'ticket_balance': ticket_balance,
                'work_income': work_income,
                'author_income': author_income
            })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 章节管理API
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_chapter(request, work_id, chapter_id):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查章节是否属于当前用户
            cursor.execute("""
                SELECT c.chapter_id FROM chapters c
                JOIN works w ON c.work_id = w.work_id
                WHERE c.chapter_id = %s AND c.work_id = %s AND w.author_id = %s
            """, [chapter_id, work_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '章节不存在或无权限'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # 删除章节
            cursor.execute("DELETE FROM chapters WHERE chapter_id = %s", [chapter_id])
            
            cursor.execute("""
                DELETE FROM collections 
                WHERE reader_id = %s AND work_id = %s
            """, [user_id, work_id])
 
            cursor.execute(
                "UPDATE works SET collect_count = GREATEST(COALESCE(collect_count, 0) - 1, 0) WHERE work_id = %s",
                [work_id]
            )
            
            detail = f"删除章节 {chapter_id}"
            _record_user_action(
                user_id,
                'delete_chapter',
                USER_ACTION_TARGET_CHAPTER,
                chapter_id,
                detail=detail,
                request=request,
                extra={'work_id': work_id}
            )
            return Response({'success': True, 'message': '章节删除成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 评论及互动 API
def _build_comment_tree(rows, root_ids):
    comment_map = {}
    order_map = {cid: idx for idx, cid in enumerate(root_ids)}

    for row in rows:
        comment_id = row[0]
        comment_map[comment_id] = {
            'comment_id': comment_id,
            'reader_id': row[1],
            'chapter_id': row[2],
            'content': row[3],
            'parent_id': row[4],
            'create_time': row[5].isoformat() if row[5] else None,
            'like_count': int(row[6] or 0),
            'liked': bool(row[7]),
            'reader_name': row[8] or '匿名读者',
            'avatar_url': row[9],
            'replies': []
        }

    for comment in comment_map.values():
        parent_id = comment['parent_id']
        if parent_id and parent_id in comment_map:
            comment_map[parent_id]['replies'].append(comment)

    for comment in comment_map.values():
        if comment['replies']:
            comment['replies'].sort(key=lambda item: (item['create_time'] or '', item['comment_id']))

    roots = []
    for cid in root_ids:
        root_comment = comment_map.get(cid)
        if root_comment:
            roots.append(root_comment)

    return roots


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work_comments(request, work_id):
    try:
        user_id = request.user.user_id
        comment_type = request.GET.get('type')
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = int(request.GET.get('page_size', 10) or 10)
        page_size = max(1, min(page_size, 50))

        with connection.cursor() as cursor:
            cursor.execute("SELECT title, author_id FROM works WHERE work_id = %s", [work_id])
            work_row = cursor.fetchone()
            if not work_row:
                return Response({'success': False, 'error': '作品不存在'}, status=status.HTTP_404_NOT_FOUND)
            work_title, author_id = work_row

        if comment_type:
            _record_user_action(
                user_id,
                'view_comments_public',
                USER_ACTION_TARGET_COMMENT,
                work_id,
                detail=f"查看作品《{work_title}》公开评论",
                request=request,
                extra={'type': comment_type, 'page': page, 'page_size': page_size}
            )
            return _get_public_comments(request, work_id, user_id, comment_type, page, page_size)

        _record_user_action(
            user_id,
            'view_comments_manage',
            USER_ACTION_TARGET_COMMENT,
            work_id,
            detail=f"管理作品《{work_title}》评论",
            request=request,
            extra={'page': page, 'page_size': page_size}
        )
        return _get_manage_comments(request, work_id, user_id, author_id, work_title, page, page_size)

    except ValueError:
        return Response({'success': False, 'error': '参数格式错误'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_public_comments(request, work_id, user_id, comment_type, page, page_size):
    chapter_id = request.GET.get('chapter_id')
    chapter_param = None

    if comment_type == 'chapter':
        if not chapter_id:
            return Response({'success': False, 'error': 'chapter_id 参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            chapter_param = int(chapter_id)
        except (TypeError, ValueError):
            return Response({'success': False, 'error': 'chapter_id 格式错误'}, status=status.HTTP_400_BAD_REQUEST)

    conditions = ["c.work_id = %s", "c.status = 1"]
    params = [work_id]

    if comment_type == 'chapter':
        conditions.append("c.chapter_id = %s")
        params.append(chapter_param)
    else:
        conditions.append("c.chapter_id IS NULL")

    root_conditions = conditions + ["c.parent_id IS NULL"]
    root_where = " AND ".join(root_conditions)

    offset = (page - 1) * page_size

    _ensure_comment_likes_table()

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM comments c WHERE {root_where}", params)
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        cursor.execute(
            f"""
            SELECT c.comment_id
            FROM comments c
            WHERE {root_where}
            ORDER BY c.create_time DESC, c.comment_id DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset]
        )
        root_ids = [row[0] for row in cursor.fetchall()]

        if not root_ids:
            return Response({
                'success': True,
                'comments': [],
                'total': total
            })

        placeholders = ','.join(['%s'] * len(root_ids))
        data_params = [user_id] + root_ids + root_ids

        cursor.execute(
            f"""
            SELECT c.comment_id, c.reader_id, c.chapter_id, c.content, c.parent_id,
                   c.create_time,
                   COALESCE(cl.like_count, 0) AS like_count,
                   CASE WHEN lk.reader_id IS NULL THEN 0 ELSE 1 END AS liked,
                   COALESCE(r.nickname, u.username, '') AS reader_name,
                   r.avatar_url
            FROM comments c
            LEFT JOIN readers r ON c.reader_id = r.reader_id
            LEFT JOIN users u ON c.reader_id = u.user_id
            LEFT JOIN (
                SELECT comment_id, COUNT(*) AS like_count
                FROM comment_likes
                GROUP BY comment_id
            ) cl ON c.comment_id = cl.comment_id
            LEFT JOIN comment_likes lk ON c.comment_id = lk.comment_id AND lk.reader_id = %s
            WHERE c.comment_id IN ({placeholders}) OR c.parent_id IN ({placeholders})
            ORDER BY c.create_time ASC, c.comment_id ASC
            """,
            data_params
        )

        rows = cursor.fetchall()

    comments = _build_comment_tree(rows, root_ids)
    has_more = (offset + len(root_ids)) < total

    return Response({
        'success': True,
        'comments': comments,
        'total': total,
        'has_more': has_more
    })


def _get_manage_comments(request, work_id, user_id, author_id, work_title, page, page_size):
    if user_id != author_id:
        return Response({'success': False, 'error': '无权查看该作品评论'}, status=status.HTTP_403_FORBIDDEN)

    status_filter = request.GET.get('status')
    conditions = ["c.work_id = %s"]
    params = [work_id]

    if status_filter not in (None, ''):
        conditions.append("c.status = %s")
        params.append(status_filter)

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * page_size

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM comments c WHERE {where_clause}", params)
        total_row = cursor.fetchone()
        total = int(total_row[0]) if total_row and total_row[0] is not None else 0

        cursor.execute(
            f"""
            SELECT c.comment_id, c.content, c.status, c.create_time,
                   COALESCE(r.nickname, u.username, '') AS reader_name,
                   r.avatar_url,
                   c.chapter_id,
                   c.parent_id
            FROM comments c
            LEFT JOIN readers r ON c.reader_id = r.reader_id
            LEFT JOIN users u ON c.reader_id = u.user_id
            WHERE {where_clause}
            ORDER BY c.create_time DESC, c.comment_id DESC
            LIMIT %s OFFSET %s
            """,
            params + [page_size, offset]
        )

        comments = []
        for row in cursor.fetchall():
            comments.append({
                'comment_id': row[0],
                'content': row[1],
                'status': row[2],
                'create_time': row[3].isoformat() if row[3] else None,
                'username': row[4],
                'user_avatar': row[5],
                'chapter_id': row[6],
                'parent_id': row[7]
            })

    return Response({
        'success': True,
        'comments': comments,
        'total': total,
        'work_title': work_title
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, work_id):
    try:
        user_id = request.user.user_id
        data = request.data or {}
        content = (data.get('content') or '').strip()
        if len(content) < 3:
            return Response({'success': False, 'error': '评论内容不能少于3个字符'}, status=status.HTTP_400_BAD_REQUEST)

        if not _user_permission_allowed(user_id, 'can_comment'):
            return Response({'success': False, 'error': '您的账号评论功能已被管理员暂停'}, status=status.HTTP_403_FORBIDDEN)

        chapter_id = data.get('chapter_id')
        parent_id = data.get('parent_id')
        chapter_value = None
        parent_value = None
        parent_reader_id = None

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT title, author_id
                FROM works
                WHERE work_id = %s
            """, [work_id])
            work_row = cursor.fetchone()
            if not work_row:
                return Response({'success': False, 'error': '作品不存在'}, status=status.HTTP_404_NOT_FOUND)

            work_title, work_author_id = work_row

            if chapter_id not in (None, '', 'null'):
                try:
                    chapter_value = int(chapter_id)
                except (TypeError, ValueError):
                    return Response({'success': False, 'error': '章节参数错误'}, status=status.HTTP_400_BAD_REQUEST)

                cursor.execute("""
                    SELECT chapter_id, status
                    FROM chapters
                    WHERE chapter_id = %s AND work_id = %s
                """, [chapter_value, work_id])
                chapter_row = cursor.fetchone()
                if not chapter_row or chapter_row[1] != 1:
                    return Response({'success': False, 'error': '章节不存在或未发布'}, status=status.HTTP_400_BAD_REQUEST)

            if parent_id not in (None, ''):
                try:
                    parent_value = int(parent_id)
                except (TypeError, ValueError):
                    return Response({'success': False, 'error': '回复目标错误'}, status=status.HTTP_400_BAD_REQUEST)

                cursor.execute("""
                    SELECT comment_id, chapter_id, reader_id
                    FROM comments
                    WHERE comment_id = %s AND work_id = %s AND status = 1
                """, [parent_value, work_id])
                parent_row = cursor.fetchone()
                if not parent_row:
                    return Response({'success': False, 'error': '回复目标不存在'}, status=status.HTTP_404_NOT_FOUND)

                if chapter_value is None:
                    chapter_value = parent_row[1]
                parent_reader_id = parent_row[2]

            cursor.execute("""
                INSERT INTO comments (reader_id, work_id, chapter_id, content, parent_id, create_time, status)
                VALUES (%s, %s, %s, %s, %s, NOW(), 1)
            """, [user_id, work_id, chapter_value, content, parent_value])

            comment_id = cursor.lastrowid

            cursor.execute("""
                SELECT c.comment_id, c.reader_id, c.chapter_id, c.content, c.parent_id,
                       c.create_time,
                       COALESCE(r.nickname, u.username, '') AS reader_name,
                       r.avatar_url
                    FROM comments c
                    LEFT JOIN readers r ON c.reader_id = r.reader_id
                    LEFT JOIN users u ON c.reader_id = u.user_id
                    WHERE c.comment_id = %s
                """, [comment_id])

            row = cursor.fetchone()

        comment_data = None
        if row:
            comment_data = {
                'comment_id': row[0],
                'reader_id': row[1],
                'chapter_id': row[2],
                'content': row[3],
                'parent_id': row[4],
                'create_time': row[5].isoformat() if row[5] else None,
                'like_count': 0,
                'liked': False,
                'reader_name': row[6] or '匿名读者',
                'avatar_url': row[7],
                'replies': []
            }

        excerpt = content[:60] + ('...' if len(content) > 60 else '')
        _record_user_action(
            user_id,
            'create_comment',
            USER_ACTION_TARGET_COMMENT,
            comment_id,
            detail=f"发表评论，作品 {work_id}",
            request=request,
            extra={
                'work_id': work_id,
                'chapter_id': chapter_value,
                'parent_id': parent_value,
                'excerpt': excerpt
            }
        )

        work_title_display = work_title or f'作品{work_id}'
        excerpt_for_message = excerpt or '新评论'
        reader_name = _get_user_display_name(user_id) or f'用户{user_id}'

        notified_users = set()

        if parent_reader_id and parent_reader_id != user_id:
            message_content = f"读者「{reader_name}」回复了你的评论：{excerpt_for_message}"
            _create_message(
                recipient_id=parent_reader_id,
                message_type=MESSAGE_TYPE_COMMENT_REPLY,
                content=message_content,
                related_type=4,
                related_id=comment_id,
                sender_id=user_id
            )
            notified_users.add(parent_reader_id)

        if work_author_id and work_author_id not in (user_id,):
            if work_author_id not in notified_users:
                message_content = f"读者「{reader_name}」在作品《{work_title_display}》发表了新的评论：{excerpt_for_message}"
                _create_message(
                    recipient_id=work_author_id,
                    message_type=MESSAGE_TYPE_COMMENT_REPLY,
                    content=message_content,
                    related_type=4,
                    related_id=comment_id,
                    sender_id=user_id
                )

        return Response({'success': True, 'comment': comment_data})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_comment(request, work_id, comment_id):
    try:
        user_id = request.user.user_id
        _ensure_comment_likes_table()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT comment_id
                FROM comments
                WHERE comment_id = %s AND work_id = %s AND status = 1
            """, [comment_id, work_id])
            if not cursor.fetchone():
                return Response({'success': False, 'error': '评论不存在'}, status=status.HTTP_404_NOT_FOUND)

            cursor.execute("""
                SELECT like_id
                FROM comment_likes
                WHERE comment_id = %s AND reader_id = %s
            """, [comment_id, user_id])
            existing = cursor.fetchone()

            if existing:
                cursor.execute("DELETE FROM comment_likes WHERE like_id = %s", [existing[0]])
                liked = False
            else:
                cursor.execute("""
                    INSERT INTO comment_likes (comment_id, reader_id, like_time)
                    VALUES (%s, %s, NOW())
                """, [comment_id, user_id])
                liked = True

            cursor.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = %s", [comment_id])
            count_row = cursor.fetchone()
            like_count = int(count_row[0]) if count_row and count_row[0] is not None else 0

        _record_user_action(
            user_id,
            'toggle_like_comment',
            USER_ACTION_TARGET_COMMENT,
            comment_id,
            detail=('点赞评论' if liked else '取消点赞评论'),
            request=request,
            extra={
                'work_id': work_id,
                'liked': liked,
                'like_count': like_count
            }
        )

        return Response({'success': True, 'like_count': like_count, 'liked': liked})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_comment(request, work_id, comment_id):
    try:
        status_value = request.data.get('status')
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.comment_id FROM comments c
                JOIN works w ON c.work_id = w.work_id
                WHERE c.comment_id = %s AND c.work_id = %s AND w.author_id = %s
            """, [comment_id, work_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '评论不存在或无权限'}, status=status.HTTP_404_NOT_FOUND)
            
            cursor.execute("""
                UPDATE comments 
                SET status = %s
                WHERE comment_id = %s
            """, [status_value, comment_id])
            
            _record_user_action(
                user_id,
                'update_comment_status',
                USER_ACTION_TARGET_COMMENT,
                comment_id,
                detail=f'更新评论状态为 {status_value}',
                request=request,
                extra={'work_id': work_id, 'status': status_value}
            )

            return Response({'success': True, 'message': '评论状态更新成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, work_id, comment_id):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.comment_id FROM comments c
                JOIN works w ON c.work_id = w.work_id
                WHERE c.comment_id = %s AND c.work_id = %s AND w.author_id = %s
            """, [comment_id, work_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '评论不存在或无权限'}, status=status.HTTP_404_NOT_FOUND)
            
            cursor.execute("DELETE FROM comment_likes WHERE comment_id = %s OR comment_id IN (SELECT comment_id FROM comments WHERE parent_id = %s)", [comment_id, comment_id])
            cursor.execute("DELETE FROM comments WHERE comment_id = %s OR parent_id = %s", [comment_id, comment_id])
            
            _record_user_action(
                user_id,
                'delete_comment',
                USER_ACTION_TARGET_COMMENT,
                comment_id,
                detail='删除评论及其回复',
                request=request,
                extra={'work_id': work_id}
            )

            return Response({'success': True, 'message': '评论删除成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 用户行为记录
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscription_records(request):
    try:
        user_id = request.user.user_id
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = min(max(int(request.GET.get('page_size', 20) or 20), 1), 100)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE reader_id = %s", [user_id])
            total_row = cursor.fetchone()
            total = int(total_row[0]) if total_row and total_row[0] is not None else 0

            cursor.execute(
                """
                SELECT s.sub_id, s.work_id, s.chapter_id, s.sub_time, s.amount,
                       w.title AS work_title,
                       ch.title AS chapter_title
                FROM subscriptions s
                LEFT JOIN works w ON s.work_id = w.work_id
                LEFT JOIN chapters ch ON s.chapter_id = ch.chapter_id
                WHERE s.reader_id = %s
                ORDER BY s.sub_time DESC, s.sub_id DESC
                LIMIT %s OFFSET %s
                """,
                [user_id, page_size, offset]
            )

            records = []
            for row in cursor.fetchall():
                records.append({
                    'sub_id': row[0],
                    'work_id': row[1],
                    'chapter_id': row[2],
                    'sub_time': row[3].isoformat() if row[3] else None,
                    'amount': float(row[4]) if row[4] is not None else 0.0,
                    'work_title': row[5] or '未知作品',
                    'chapter_title': row[6]
                })

        return Response({'success': True, 'records': records, 'total': total})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_vote_records(request):
    try:
        user_id = request.user.user_id
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = min(max(int(request.GET.get('page_size', 20) or 20), 1), 100)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM votes WHERE reader_id = %s", [user_id])
            total_row = cursor.fetchone()
            total = int(total_row[0]) if total_row and total_row[0] is not None else 0

            cursor.execute(
                """
                SELECT v.vote_id, v.work_id, v.vote_time, v.count, v.message,
                       w.title AS work_title
                FROM votes v
                LEFT JOIN works w ON v.work_id = w.work_id
                WHERE v.reader_id = %s
                ORDER BY v.vote_time DESC, v.vote_id DESC
                LIMIT %s OFFSET %s
                """,
                [user_id, page_size, offset]
            )

            records = []
            for row in cursor.fetchall():
                records.append({
                    'vote_id': row[0],
                    'work_id': row[1],
                    'vote_time': row[2].isoformat() if row[2] else None,
                    'count': int(row[3] or 0),
                    'message': row[4],
                    'work_title': row[5] or '未知作品'
                })

        return Response({'success': True, 'records': records, 'total': total})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_work_vote_records(request, work_id):
    try:
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = min(max(int(request.GET.get('page_size', 20) or 20), 1), 100)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM votes WHERE work_id = %s", [work_id])
            total_row = cursor.fetchone()
            total = int(total_row[0]) if total_row and total_row[0] is not None else 0

            cursor.execute(
                """
                SELECT v.vote_id, v.reader_id, v.vote_time, v.count, v.message,
                       COALESCE(r.nickname, u.username, '') AS reader_name
                FROM votes v
                LEFT JOIN readers r ON v.reader_id = r.reader_id
                LEFT JOIN users u ON v.reader_id = u.user_id
                WHERE v.work_id = %s
                ORDER BY v.vote_time DESC, v.vote_id DESC
                LIMIT %s OFFSET %s
                """,
                [work_id, page_size, offset]
            )

            records = []
            for row in cursor.fetchall():
                records.append({
                    'vote_id': row[0],
                    'reader_id': row[1],
                    'vote_time': row[2].isoformat() if row[2] else None,
                    'count': int(row[3] or 0),
                    'message': row[4],
                    'reader_name': row[5] or '匿名读者'
                })

        return Response({'success': True, 'records': records, 'total': total})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_history(request):
    try:
        user_id = request.user.user_id
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = min(max(int(request.GET.get('page_size', 20) or 20), 1), 100)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM comments WHERE reader_id = %s", [user_id])
            total_row = cursor.fetchone()
            total = int(total_row[0]) if total_row and total_row[0] is not None else 0

            cursor.execute(
                """
                SELECT c.comment_id, c.work_id, c.chapter_id, c.parent_id, c.content, c.create_time,
                       w.title AS work_title,
                       ch.title AS chapter_title
                FROM comments c
                LEFT JOIN works w ON c.work_id = w.work_id
                LEFT JOIN chapters ch ON c.chapter_id = ch.chapter_id
                WHERE c.reader_id = %s
                ORDER BY c.create_time DESC, c.comment_id DESC
                LIMIT %s OFFSET %s
                """,
                [user_id, page_size, offset]
            )

            records = []
            for row in cursor.fetchall():
                records.append({
                    'comment_id': row[0],
                    'work_id': row[1],
                    'chapter_id': row[2],
                    'parent_id': row[3],
                    'content': row[4],
                    'create_time': row[5].isoformat() if row[5] else None,
                    'work_title': row[6] or '未知作品',
                    'chapter_title': row[7],
                    'is_book_comment': row[2] is None,
                    'is_reply': row[3] is not None
                })

        return Response({'success': True, 'records': records, 'total': total})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_thread(request, comment_id):
    try:
        user_id = request.user.user_id
        _ensure_comment_likes_table()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT comment_id, reader_id, work_id, chapter_id, content, parent_id, create_time
                FROM comments
                WHERE comment_id = %s
            """, [comment_id])
            comment_row = cursor.fetchone()

            if not comment_row:
                return Response({'success': False, 'error': '评论不存在'}, status=status.HTTP_404_NOT_FOUND)

            root_id = comment_row[0] if comment_row[5] is None else comment_row[5]

            cursor.execute("""
                SELECT c.comment_id, c.reader_id, c.chapter_id, c.content, c.parent_id, c.create_time,
                       COALESCE(cl.like_count, 0) AS like_count,
                       CASE WHEN lk.reader_id IS NULL THEN 0 ELSE 1 END AS liked,
                       COALESCE(r.nickname, u.username, '') AS reader_name,
                       r.avatar_url
                FROM comments c
                LEFT JOIN readers r ON c.reader_id = r.reader_id
                LEFT JOIN users u ON c.reader_id = u.user_id
                LEFT JOIN (
                    SELECT comment_id, COUNT(*) AS like_count
                    FROM comment_likes
                    GROUP BY comment_id
                ) cl ON c.comment_id = cl.comment_id
                LEFT JOIN comment_likes lk ON c.comment_id = lk.comment_id AND lk.reader_id = %s
                WHERE c.comment_id = %s
            """, [user_id, root_id])
            root_row = cursor.fetchone()

            if not root_row:
                return Response({'success': False, 'error': '评论不存在'}, status=status.HTTP_404_NOT_FOUND)

            cursor.execute("""
                SELECT c.comment_id, c.reader_id, c.chapter_id, c.content, c.parent_id, c.create_time,
                       COALESCE(cl.like_count, 0) AS like_count,
                       CASE WHEN lk.reader_id IS NULL THEN 0 ELSE 1 END AS liked,
                       COALESCE(r.nickname, u.username, '') AS reader_name,
                       r.avatar_url
                FROM comments c
                LEFT JOIN readers r ON c.reader_id = r.reader_id
                LEFT JOIN users u ON c.reader_id = u.user_id
                LEFT JOIN (
                    SELECT comment_id, COUNT(*) AS like_count
                    FROM comment_likes
                    GROUP BY comment_id
                ) cl ON c.comment_id = cl.comment_id
                LEFT JOIN comment_likes lk ON c.comment_id = lk.comment_id AND lk.reader_id = %s
                WHERE c.parent_id = %s
                ORDER BY c.create_time ASC, c.comment_id ASC
            """, [user_id, root_id])

            replies = []
            for row in cursor.fetchall():
                replies.append({
                    'comment_id': row[0],
                    'reader_id': row[1],
                    'chapter_id': row[2],
                    'content': row[3],
                    'parent_id': row[4],
                    'create_time': row[5].isoformat() if row[5] else None,
                    'like_count': int(row[6] or 0),
                    'liked': bool(row[7]),
                    'reader_name': row[8] or '匿名读者',
                    'avatar_url': row[9]
                })

        thread = {
            'comment_id': root_row[0],
            'reader_id': root_row[1],
            'chapter_id': root_row[2],
            'content': root_row[3],
            'parent_id': root_row[4],
            'create_time': root_row[5].isoformat() if root_row[5] else None,
            'like_count': int(root_row[6] or 0),
            'liked': bool(root_row[7]),
            'reader_name': root_row[8] or '匿名读者',
            'avatar_url': root_row[9],
            'replies': replies
        }

        return Response({'success': True, 'thread': thread})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_comment(request, comment_id):
    try:
        user_id = request.user.user_id
        _ensure_comment_likes_table()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT comment_id, COALESCE(parent_id, comment_id) AS root_id
                FROM comments
                WHERE comment_id = %s AND reader_id = %s
            """, [comment_id, user_id])
            comment_row = cursor.fetchone()

            if not comment_row:
                return Response({'success': False, 'error': '评论不存在或无权删除'}, status=status.HTTP_404_NOT_FOUND)

            root_id = comment_row[1]

            cursor.execute("DELETE FROM comment_likes WHERE comment_id = %s OR comment_id IN (SELECT comment_id FROM comments WHERE parent_id = %s)", [root_id, root_id])
            cursor.execute("DELETE FROM comments WHERE comment_id = %s OR parent_id = %s", [root_id, root_id])

        return Response({'success': True, 'message': '评论已删除'})

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 书架相关API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookshelf(request):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 获取收藏的作品
            cursor.execute("""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.status,
                       a.pen_name, cat.name as category_name, c.collect_time
                FROM collections c
                JOIN works w ON c.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN categories cat ON w.category_id = cat.category_id
                WHERE c.reader_id = %s
                ORDER BY c.collect_time DESC
            """, [user_id])
            
            collections = []
            for row in cursor.fetchall():
                collections.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'intro': row[3],
                    'status': row[4],
                    'author_name': row[5],
                    'category_name': row[6],
                    'collect_time': row[7].isoformat() if row[7] else None
                })
            
            return Response({'success': True, 'collections': collections})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_bookshelf(request):
    try:
        data = request.data
        user_id = request.user.user_id
        work_id = data.get('work_id')
        
        if not work_id:
            return Response({'success': False, 'error': '作品ID不能为空'})
        
        with connection.cursor() as cursor:
            # 检查是否已收藏
            cursor.execute("""
                SELECT collection_id FROM collections 
                WHERE reader_id = %s AND work_id = %s
            """, [user_id, work_id])
            
            if cursor.fetchone():
                return Response({'success': False, 'error': '已收藏该作品'})
            
            # 添加收藏
            cursor.execute("""
                INSERT INTO collections (reader_id, work_id, collect_time)
                VALUES (%s, %s, NOW())
            """, [user_id, work_id])
 
            cursor.execute(
                "UPDATE works SET collect_count = COALESCE(collect_count, 0) + 1 WHERE work_id = %s",
                [work_id]
            )
 
            _record_user_action(
                user_id,
                'add_to_bookshelf',
                USER_ACTION_TARGET_BOOKSHELF,
                work_id,
                detail='收藏作品到书架',
                request=request
            )

            _record_recommendation_feedback(
                user_id,
                work_id,
                FEEDBACK_EVENT_COLLECT,
                weight_delta=1.0,
                metadata={'source': 'bookshelf'}
            )

            return Response({'success': True, 'message': '收藏成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_bookshelf(request, work_id):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查是否已收藏
            cursor.execute("""
                SELECT collection_id FROM collections 
                WHERE reader_id = %s AND work_id = %s
            """, [user_id, work_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '未收藏该作品'})
            
            # 移除收藏
            cursor.execute("""
                DELETE FROM collections 
                WHERE reader_id = %s AND work_id = %s
            """, [user_id, work_id])
 
            cursor.execute(
                "UPDATE works SET collect_count = GREATEST(COALESCE(collect_count, 0) - 1, 0) WHERE work_id = %s",
                [work_id]
            )
 
            _record_user_action(
                user_id,
                'remove_from_bookshelf',
                USER_ACTION_TARGET_BOOKSHELF,
                work_id,
                detail='从书架移除作品',
                request=request
            )

            return Response({'success': True, 'message': '移除成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 阅读记录API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reading_history(request):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT w.work_id, w.title, w.cover_url, a.pen_name,
                       MAX(rr.read_time) as last_read_time
                FROM reading_records rr
                JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                JOIN works w ON ch.work_id = w.work_id
                LEFT JOIN authors a ON w.author_id = a.author_id
                WHERE rr.reader_id = %s
                GROUP BY w.work_id, w.title, w.cover_url, a.pen_name
                ORDER BY last_read_time DESC
            """, [user_id])
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'author_name': row[3],
                    'last_read_time': row[4].isoformat() if row[4] else None
                })
            
            return Response({'success': True, 'history': history})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 排行榜API
@api_view(['GET'])
def get_rankings(request):
    try:
        ranking_type = request.GET.get('type', 'read')
        category_id = request.GET.get('category_id')
        period = request.GET.get('period', 'week')

        allowed_types = {'read', 'vote', 'subscribe'}
        if ranking_type not in allowed_types:
            ranking_type = 'read'

        allowed_periods = {'day', 'week', 'month', 'total'}
        if period not in allowed_periods:
            period = 'week'

        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            category_id = None

        now = timezone.now()
        start_time = None
        if period == 'day':
            start_time = now - timedelta(days=1)
        elif period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'month':
            start_time = now - timedelta(days=30)

        with connection.cursor() as cursor:
            base_conditions = ["w.status IN (1, 2)"]
            main_params = []

            if category_id is not None:
                base_conditions.append("w.category_id = %s")
                main_params.append(category_id)

            where_clause = " AND ".join(base_conditions)

            query = ""
            query_params = []

            if ranking_type == 'read':
                time_condition = ""
                time_params = []
                if start_time:
                    time_condition = "WHERE rr.read_time >= %s"
                    time_params.append(start_time)
                query = f"""
                    SELECT w.work_id, w.title, w.cover_url, a.pen_name,
                           COALESCE(r.read_count, 0) AS score
                    FROM works w
                    LEFT JOIN authors a ON w.author_id = a.author_id
                    LEFT JOIN (
                        SELECT ch.work_id, COUNT(*) AS read_count
                        FROM reading_records rr
                        JOIN chapters ch ON rr.chapter_id = ch.chapter_id
                        {time_condition}
                        GROUP BY ch.work_id
                    ) r ON w.work_id = r.work_id
                    WHERE {where_clause}
                    ORDER BY score DESC, w.update_time DESC, w.work_id ASC
                    LIMIT 50
                """
                query_params = time_params + main_params
            elif ranking_type == 'vote':
                time_condition = ""
                time_params = []
                if start_time:
                    time_condition = "WHERE v.vote_time >= %s"
                    time_params.append(start_time.date())
                query = f"""
                    SELECT w.work_id, w.title, w.cover_url, a.pen_name,
                           COALESCE(vt.vote_count, 0) AS score
                    FROM works w
                    LEFT JOIN authors a ON w.author_id = a.author_id
                    LEFT JOIN (
                        SELECT work_id, SUM(count) AS vote_count
                        FROM votes v
                        {time_condition}
                        GROUP BY work_id
                    ) vt ON w.work_id = vt.work_id
                    WHERE {where_clause}
                    ORDER BY score DESC, w.update_time DESC, w.work_id ASC
                    LIMIT 50
                """
                query_params = time_params + main_params
            else:  # subscribe
                time_condition = ""
                time_params = []
                if start_time:
                    time_condition = "WHERE s.sub_time >= %s"
                    time_params.append(start_time)
                query = f"""
                    SELECT w.work_id, w.title, w.cover_url, a.pen_name,
                           COALESCE(st.sub_amount, 0) AS score
                    FROM works w
                    LEFT JOIN authors a ON w.author_id = a.author_id
                    LEFT JOIN (
                        SELECT work_id, SUM(amount) AS sub_amount
                        FROM subscriptions s
                        {time_condition}
                        GROUP BY work_id
                    ) st ON w.work_id = st.work_id
                    WHERE {where_clause}
                    ORDER BY score DESC, w.update_time DESC, w.work_id ASC
                    LIMIT 50
                """
                query_params = time_params + main_params

            cursor.execute(query, query_params)

            rankings = []
            for row in cursor.fetchall():
                raw_score = row[4]
                if raw_score is None:
                    score = 0
                elif isinstance(raw_score, Decimal):
                    score = float(raw_score)
                elif isinstance(raw_score, float):
                    score = int(raw_score) if raw_score.is_integer() else raw_score
                else:
                    score = int(raw_score)
                rankings.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'author_name': row[3] or '',
                    'score': score
                })

            return Response({'success': True, 'rankings': rankings})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 消息通知API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request):
    try:
        user_id = request.user.user_id
        message_type = request.GET.get('type')
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = int(request.GET.get('page_size', 20) or 20)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size
        
        with connection.cursor() as cursor:
            where_conditions = ["recipient_id = %s"]
            params = [user_id]
            
            if message_type:
                where_conditions.append("message_type = %s")
                params.append(message_type)
            
            where_clause = " AND ".join(where_conditions)

            cursor.execute(
                f"SELECT COUNT(*) FROM messages WHERE {where_clause}",
                params
            )
            total_row = cursor.fetchone()
            total_count = int(total_row[0]) if total_row and total_row[0] is not None else 0

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE recipient_id = %s AND is_read = 0
                """,
                [user_id]
            )
            unread_row = cursor.fetchone()
            unread_count = int(unread_row[0]) if unread_row and unread_row[0] is not None else 0

            cursor.execute(
                """
                SELECT message_type, COUNT(*)
                FROM messages
                WHERE recipient_id = %s AND is_read = 0
                GROUP BY message_type
                """,
                [user_id]
            )
            type_counts = {}
            for row in cursor.fetchall():
                type_key = str(row[0]) if row[0] is not None else ''
                type_counts[type_key] = int(row[1] or 0)
            
            cursor.execute(f"""
                SELECT message_id, sender_id, message_type, content, 
                       related_type, related_id, is_read, send_time
                FROM messages
                WHERE {where_clause}
                ORDER BY send_time DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            
            messages = []
            for row in cursor.fetchall():
                message_type_value = row[2]
                message_type_str = str(message_type_value) if message_type_value is not None else ''
                messages.append({
                    'message_id': row[0],
                    'sender_id': row[1],
                    'message_type': message_type_str,
                    'content': row[3],
                    'related_type': row[4],
                    'related_id': row[5],
                    'is_read': row[6],
                    'send_time': row[7].isoformat() if row[7] else None
                })
            
            return Response({
                'success': True,
                'messages': messages,
                'total': total_count,
                'unread_count': unread_count,
                'type_counts': type_counts
            })
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 搜索API
@api_view(['GET'])
def search_works(request):
    try:
        keyword = (request.GET.get('keyword') or '').strip()
        category_id = request.GET.get('category_id')
        author_name = (request.GET.get('author_name') or '').strip()
        status_param = request.GET.get('status')
        word_count_min = request.GET.get('word_count_min')
        word_count_max = request.GET.get('word_count_max')
        page = max(int(request.GET.get('page', 1) or 1), 1)
        page_size = int(request.GET.get('page_size', 20) or 20)
        page_size = max(1, min(page_size, 50))
        offset = (page - 1) * page_size
        user = getattr(request, 'user', None)
        user_id = getattr(user, 'user_id', None) if getattr(user, 'is_authenticated', False) else None

        with connection.cursor() as cursor:
            search_term = keyword if keyword else author_name
            if user_id and search_term:
                _ensure_search_records_table()
                search_type = 1
                if author_name and search_term == author_name and not keyword:
                    search_type = 2
                elif keyword.startswith('#'):
                    search_type = 3

                cursor.execute(
                    "DELETE FROM search_records WHERE reader_id = %s AND keyword = %s",
                    [user_id, search_term]
                )
                cursor.execute(
                    """
                    INSERT INTO search_records (reader_id, keyword, search_type, search_time)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    [user_id, search_term, search_type]
                )

                # 限制历史记录长度
                cursor.execute(
                    """
                    DELETE FROM search_records
                    WHERE reader_id = %s AND search_id NOT IN (
                        SELECT search_id FROM (
                            SELECT search_id
                            FROM search_records
                            WHERE reader_id = %s
                            ORDER BY search_time DESC
                            LIMIT 100
                        ) recent
                    )
                    """,
                    [user_id, user_id]
                )

            where_conditions = ["w.status IN (1, 2)"]
            params = []

            if keyword:
                like_keyword = f'%{keyword}%'
                where_conditions.append("(w.title LIKE %s OR w.intro LIKE %s OR COALESCE(a.pen_name, '') LIKE %s OR COALESCE(u.username, '') LIKE %s)")
                params.extend([like_keyword, like_keyword, like_keyword, like_keyword])

            if category_id not in (None, '', 'all'):
                try:
                    category_value = int(category_id)
                    where_conditions.append("w.category_id = %s")
                    params.append(category_value)
                except (TypeError, ValueError):
                    pass

            if author_name:
                like_author = f'%{author_name}%'
                where_conditions.append("(COALESCE(a.pen_name, '') LIKE %s OR COALESCE(r.nickname, '') LIKE %s OR COALESCE(u.username, '') LIKE %s)")
                params.extend([like_author, like_author, like_author])

            if status_param not in (None, '', 'all'):
                try:
                    status_value = int(status_param)
                    if status_value in (1, 2):
                        where_conditions.append("w.status = %s")
                        params.append(status_value)
                except (TypeError, ValueError):
                    pass

            if word_count_min not in (None, '', 'null'):
                try:
                    min_words = int(word_count_min)
                    if min_words >= 0:
                        where_conditions.append("COALESCE(cw.total_words, 0) >= %s")
                        params.append(min_words)
                except (TypeError, ValueError):
                    pass

            if word_count_max not in (None, '', 'null'):
                try:
                    max_words = int(word_count_max)
                    if max_words >= 0:
                        where_conditions.append("COALESCE(cw.total_words, 0) <= %s")
                        params.append(max_words)
                except (TypeError, ValueError):
                    pass

            where_clause = " AND ".join(where_conditions) if where_conditions else "1 = 1"

            base_query = f"""
                FROM works w
                LEFT JOIN authors a ON w.author_id = a.author_id
                LEFT JOIN readers r ON w.author_id = r.reader_id
                LEFT JOIN users u ON w.author_id = u.user_id
                LEFT JOIN categories c ON w.category_id = c.category_id
                LEFT JOIN (
                    SELECT work_id, SUM(word_count) AS total_words
                    FROM chapters
                    WHERE status = 1
                    GROUP BY work_id
                ) cw ON w.work_id = cw.work_id
                WHERE {where_clause}
            """

            count_query = f"SELECT COUNT(*) {base_query}"
            cursor.execute(count_query, params.copy())
            total_row = cursor.fetchone()
            total = int(total_row[0]) if total_row and total_row[0] is not None else 0

            data_query = f"""
                SELECT w.work_id, w.title, w.cover_url, w.intro, w.create_time,
                       COALESCE(a.pen_name, r.nickname, u.username, '') AS author_name,
                       COALESCE(c.name, '') AS category_name,
                       w.status,
                       COALESCE(cw.total_words, 0) AS total_words,
                       w.update_time,
                       COALESCE(w.read_count, 0) AS read_count,
                       COALESCE(w.collect_count, 0) AS collect_count,
                       COALESCE(w.vote_count, 0) AS vote_count,
                       w.category_id
                {base_query}
                ORDER BY w.update_time DESC, w.create_time DESC
                LIMIT %s OFFSET %s
            """

            data_params = params.copy()
            data_params.extend([page_size, offset])
            cursor.execute(data_query, data_params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'work_id': row[0],
                    'title': row[1],
                    'cover_url': row[2],
                    'intro': row[3],
                    'create_time': row[4].isoformat() if row[4] else None,
                    'author_name': row[5],
                    'category_name': row[6],
                    'status': row[7],
                    'word_count': int(row[8] or 0),
                    'update_time': row[9].isoformat() if row[9] else None,
                    'read_count': int(row[10] or 0),
                    'collect_count': int(row[11] or 0),
                    'vote_count': int(row[12] or 0),
                    'category_id': row[13]
                })

            return Response({
                'success': True,
                'results': results,
                'total': total,
                'page': page,
                'page_size': page_size
            })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_message_read(request, message_id):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查消息是否属于当前用户
            cursor.execute("""
                SELECT message_id FROM messages 
                WHERE message_id = %s AND recipient_id = %s
            """, [message_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '消息不存在或无权限'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # 标记为已读
            cursor.execute("""
                UPDATE messages 
                SET is_read = 1
                WHERE message_id = %s
            """, [message_id])
            
            return Response({'success': True, 'message': '消息已标记为已读'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_all_messages_read(request):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 标记所有消息为已读
            cursor.execute("""
                UPDATE messages 
                SET is_read = 1
                WHERE recipient_id = %s AND is_read = 0
            """, [user_id])
            
            return Response({'success': True, 'message': '所有消息已标记为已读'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    try:
        user_id = request.user.user_id
        
        with connection.cursor() as cursor:
            # 检查消息是否属于当前用户
            cursor.execute("""
                SELECT message_id FROM messages 
                WHERE message_id = %s AND recipient_id = %s
            """, [message_id, user_id])
            
            if not cursor.fetchone():
                return Response({'success': False, 'error': '消息不存在或无权限'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # 删除消息
            cursor.execute("DELETE FROM messages WHERE message_id = %s", [message_id])
            
            return Response({'success': True, 'message': '消息删除成功'})
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 点券和投票系统API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_points(request):
    try:
        user_id = request.user.user_id

        _ensure_point_transactions_table()
        _ensure_user_tickets_table()

        with connection.cursor() as cursor:
            cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
            balance_row = cursor.fetchone()
            balance_value = Decimal('0')
            if balance_row and balance_row[0] is not None:
                balance_value = Decimal(str(balance_row[0]))

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM point_transactions WHERE user_id = %s", [user_id])
            total_points_row = cursor.fetchone()
            total_points = Decimal(str(total_points_row[0])) if total_points_row and total_points_row[0] is not None else Decimal('0')

            _ensure_user_ticket_wallet(cursor, user_id)
            cursor.execute("SELECT ticket_balance FROM user_tickets WHERE user_id = %s", [user_id])
            ticket_row = cursor.fetchone()
            ticket_balance = int(ticket_row[0]) if ticket_row and ticket_row[0] is not None else 0

            cursor.execute("""
                SELECT transaction_type, amount, description, create_time
                FROM point_transactions 
                WHERE user_id = %s
                ORDER BY create_time DESC
                LIMIT 10
            """, [user_id])
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'transaction_type': row[0],
                    'amount': float(row[1]),
                    'description': row[2],
                    'create_time': row[3].isoformat() if row[3] else None
                })
            
            return Response({
                'success': True,
                'balance': float(balance_value),
                'ticket_count': ticket_balance,
                'total_points': float(total_points),
                'transactions': transactions
            })
            
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_work(request, work_id):
    try:
        data = request.data
        user_id = request.user.user_id
        ticket_count = int(data.get('ticket_count', 1))
        vote_message = data.get('message', '')
        
        if ticket_count <= 0:
            return Response({'success': False, 'error': '投票数量必须大于0'})
        
        if not _user_permission_allowed(user_id, 'can_vote'):
            return Response({'success': False, 'error': '您的账号投票权限已被暂停'}, status=status.HTTP_403_FORBIDDEN)

        _ensure_user_tickets_table()

        author_id = None
        work_title = ''

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT author_id, title
                FROM works
                WHERE work_id = %s
                """,
                [work_id]
            )
            work_row = cursor.fetchone()
            if not work_row:
                return Response({'success': False, 'error': '作品不存在'}, status=status.HTTP_404_NOT_FOUND)
            author_id, work_title = work_row

            cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
            reader_row = cursor.fetchone()
            if not reader_row:
                return Response({'success': False, 'error': '读者信息不存在'}, status=status.HTTP_404_NOT_FOUND)

            moderation = _get_work_moderation(work_id)
            if moderation.get('is_hidden'):
                return Response({'success': False, 'error': '作品已被管理员屏蔽，暂无法投票'}, status=status.HTTP_403_FORBIDDEN)
            if moderation.get('votes_blocked'):
                return Response({'success': False, 'error': '作品投票功能已被管理员暂停'}, status=status.HTTP_403_FORBIDDEN)

            balance_value = reader_row[0] if reader_row[0] is not None else Decimal('0')
            if not isinstance(balance_value, Decimal):
                balance_value = Decimal(str(balance_value))

            cursor.execute("START TRANSACTION")

            try:
                _ensure_user_ticket_wallet(cursor, user_id)
                cursor.execute(
                    "SELECT ticket_balance FROM user_tickets WHERE user_id = %s FOR UPDATE",
                    [user_id]
                )
                ticket_row = cursor.fetchone()
                available_tickets = int(ticket_row[0]) if ticket_row and ticket_row[0] is not None else 0

                if available_tickets < ticket_count:
                    cursor.execute("ROLLBACK")
                    return Response({
                        'success': False,
                        'error': f'月票数量不足，当前仅有 {available_tickets} 张'
                    }, status=status.HTTP_400_BAD_REQUEST)

                cursor.execute(
                    """
                    UPDATE user_tickets
                    SET ticket_balance = ticket_balance - %s,
                        total_spent = total_spent + %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    [ticket_count, ticket_count, user_id]
                )

                cursor.execute("""
                    INSERT INTO votes (reader_id, work_id, vote_type, vote_time, count, message)
                    VALUES (%s, %s, 1, NOW(), %s, %s)
                """, [user_id, work_id, ticket_count, vote_message])

                cursor.execute("""
                    UPDATE works 
                    SET vote_count = COALESCE(vote_count, 0) + %s
                    WHERE work_id = %s
                """, [ticket_count, work_id])

                cursor.execute("COMMIT")

                cursor.execute("SELECT ticket_balance FROM user_tickets WHERE user_id = %s", [user_id])
                remaining_row = cursor.fetchone()
                remaining_tickets = int(remaining_row[0]) if remaining_row and remaining_row[0] is not None else 0

                cursor.execute("SELECT balance FROM readers WHERE reader_id = %s", [user_id])
                new_balance_row = cursor.fetchone()
                new_balance = float(new_balance_row[0]) if new_balance_row and new_balance_row[0] is not None else float(balance_value)

                _record_recommendation_feedback(
                    user_id,
                    work_id,
                    FEEDBACK_EVENT_VOTE,
                    weight_delta=1.0,
                    metadata={'ticket_count': ticket_count, 'message': vote_message}
                )

                if author_id and author_id != user_id:
                    reader_name = _get_user_display_name(user_id) or f'用户{user_id}'
                    work_title_display = work_title or f'作品{work_id}'
                    vote_message_text = (vote_message or '').strip()
                    message_content = f"读者「{reader_name}」为作品《{work_title_display}》投出了 {ticket_count} 张月票"
                    if vote_message_text:
                        message_content += f'，留言：“{vote_message_text}”'
                    message_content += '。'
                    _create_message(
                        recipient_id=author_id,
                        message_type=MESSAGE_TYPE_VOTE,
                        content=message_content,
                        related_type=2,
                        related_id=work_id,
                        sender_id=user_id
                    )

                return Response({
                    'success': True,
                    'message': f'投票成功，消耗 {ticket_count} 张月票',
                    'balance': new_balance,
                    'ticket_count': ticket_count,
                    'remaining_tickets': remaining_tickets
                })

            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
                
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_points(request):
    try:
        data = request.data
        user_id = request.user.user_id
        amount = int(data.get('amount', 0))
        
        if amount <= 0:
            return Response({'success': False, 'error': '购买金额必须大于0'})

        if not _user_permission_allowed(user_id, 'can_recharge'):
            return Response({'success': False, 'error': '您的账号充值功能已被管理员暂停'}, status=status.HTTP_403_FORBIDDEN)
        
        _ensure_point_transactions_table()

        with connection.cursor() as cursor:
            amount_decimal = Decimal(str(amount))
            cursor.execute("START TRANSACTION")

            try:
                cursor.execute(
                    "UPDATE readers SET balance = COALESCE(balance, 0) + %s WHERE reader_id = %s",
                    [amount_decimal, user_id]
                )

                cursor.execute("""
                    INSERT INTO point_transactions (user_id, transaction_type, amount, description, create_time)
                    VALUES (%s, 'purchase', %s, %s, NOW())
                """, [user_id, amount_decimal, f'购买{amount}点券'])

                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise

        return Response({
            'success': True,
            'message': f'购买成功，获得{amount}点券'
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)