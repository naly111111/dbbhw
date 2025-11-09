from django.db import models

# 用户基础表
class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.CharField(max_length=100, unique=True, null=True, blank=True)
    role = models.SmallIntegerField()  # 1=读者，2=作者，3=编辑
    status = models.SmallIntegerField(default=1)  # 1=正常，0=禁用
    create_time = models.DateTimeField(auto_now_add=True)
    last_login_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'

# 读者信息表
class Reader(models.Model):
    reader_id = models.BigIntegerField(primary_key=True)
    nickname = models.CharField(max_length=50)
    avatar_url = models.CharField(max_length=500, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'readers'

# 作者信息表
class Author(models.Model):
    author_id = models.BigIntegerField(primary_key=True)
    pen_name = models.CharField(max_length=50, unique=True)
    intro = models.TextField(blank=True)
    identity_status = models.SmallIntegerField(default=0)  # 0=未认证，1=已认证
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'authors'

# 编辑信息表
class Editor(models.Model):
    editor_id = models.BigIntegerField(primary_key=True)
    real_name = models.CharField(max_length=50)
    department = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'editors'

# 作品类别表
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    parent_id = models.IntegerField(null=True, blank=True)
    sort_num = models.IntegerField(default=0)

    class Meta:
        db_table = 'categories'

# 作品表
class Work(models.Model):
    work_id = models.BigAutoField(primary_key=True)
    author_id = models.BigIntegerField()
    category_id = models.IntegerField()
    title = models.CharField(max_length=200)
    cover_url = models.CharField(max_length=500, blank=True)
    intro = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    status = models.SmallIntegerField(default=0)  # 0=草稿，1=连载中，2=完结，3=下架
    is_signed = models.SmallIntegerField(default=0)  # 0=未签约，1=已签约
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'works'

# 章节表
class Chapter(models.Model):
    chapter_id = models.BigAutoField(primary_key=True)
    work_id = models.BigIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()
    intro = models.TextField(blank=True)
    word_count = models.IntegerField()
    is_free = models.SmallIntegerField(default=1)  # 1=免费，0=付费
    chapter_order = models.IntegerField()
    status = models.SmallIntegerField(default=0)  # 0=草稿，1=已发布，2=已下架
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    publish_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chapters'

# 收藏记录表
class Collection(models.Model):
    collection_id = models.BigAutoField(primary_key=True)
    reader_id = models.BigIntegerField()
    work_id = models.BigIntegerField()
    collect_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collections'
        unique_together = ('reader_id', 'work_id')

# 阅读记录表
class ReadingRecord(models.Model):
    record_id = models.BigAutoField(primary_key=True)
    reader_id = models.BigIntegerField()
    chapter_id = models.BigIntegerField()
    read_time = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # 阅读进度百分比
    is_finished = models.SmallIntegerField(default=0)  # 是否读完

    class Meta:
        db_table = 'reading_records'

# 订阅记录表
class Subscription(models.Model):
    sub_id = models.BigAutoField(primary_key=True)
    reader_id = models.BigIntegerField()
    work_id = models.BigIntegerField()
    chapter_id = models.BigIntegerField(null=True, blank=True)  # NULL表示全本订阅
    sub_time = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'subscriptions'

# 投票记录表
class Vote(models.Model):
    vote_id = models.BigAutoField(primary_key=True)
    reader_id = models.BigIntegerField()
    work_id = models.BigIntegerField()
    vote_type = models.SmallIntegerField()  # 1=月票，2=推荐票
    vote_time = models.DateField()
    count = models.IntegerField(default=1)

    class Meta:
        db_table = 'votes'
        unique_together = ('reader_id', 'work_id', 'vote_type', 'vote_time')

# 评论表
class Comment(models.Model):
    comment_id = models.BigAutoField(primary_key=True)
    reader_id = models.BigIntegerField()
    work_id = models.BigIntegerField()
    chapter_id = models.BigIntegerField(null=True, blank=True)
    content = models.TextField()
    parent_id = models.BigIntegerField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(default=1)  # 1=正常，0=删除

    class Meta:
        db_table = 'comments'

# 消息表
class Message(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    sender_id = models.BigIntegerField(null=True, blank=True)
    recipient_id = models.BigIntegerField()
    message_type = models.IntegerField()
    content = models.TextField()
    related_type = models.SmallIntegerField(null=True, blank=True)
    related_id = models.BigIntegerField(null=True, blank=True)
    is_read = models.SmallIntegerField(default=0)
    send_time = models.DateTimeField(auto_now_add=True)
    expire_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messages'

class Admin(models.Model):
    admin_id = models.BigIntegerField(primary_key=True)
    display_name = models.CharField(max_length=100)
    status = models.SmallIntegerField(default=1)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admins'

class UserPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, db_column='user_id')
    can_publish = models.SmallIntegerField(default=1)
    can_subscribe = models.SmallIntegerField(default=1)
    can_recharge = models.SmallIntegerField(default=1)
    can_comment = models.SmallIntegerField(default=1)
    can_vote = models.SmallIntegerField(default=1)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_permissions'

class WorkModeration(models.Model):
    work = models.OneToOneField(Work, on_delete=models.CASCADE, primary_key=True, db_column='work_id')
    is_hidden = models.SmallIntegerField(default=0)
    chapters_blocked = models.SmallIntegerField(default=0)
    updates_blocked = models.SmallIntegerField(default=0)
    subscriptions_blocked = models.SmallIntegerField(default=0)
    votes_blocked = models.SmallIntegerField(default=0)
    note = models.TextField(blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'work_moderations'


class AdminActionLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    admin_id = models.BigIntegerField()
    target_type = models.SmallIntegerField()
    target_id = models.BigIntegerField()
    action = models.CharField(max_length=100)
    detail = models.TextField(blank=True)
    extra_data = models.TextField(blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    user_agent = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_action_logs'


class UserActionLog(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    action = models.CharField(max_length=100)
    target_type = models.SmallIntegerField(null=True, blank=True)
    target_id = models.BigIntegerField(null=True, blank=True)
    detail = models.TextField(blank=True)
    extra_data = models.TextField(blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    user_agent = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_action_logs'

# 榜单表
class Ranking(models.Model):
    ranking_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    category_id = models.IntegerField(null=True, blank=True)
    period = models.SmallIntegerField()  # 1=日榜，2=周榜，3=月榜，4=总榜
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    source_type = models.JSONField()
    status = models.SmallIntegerField(default=1)
    sort_rule = models.CharField(max_length=50, default='score DESC')
    display_limit = models.IntegerField(default=100)

    class Meta:
        db_table = 'rankings'

# 榜单详情表
class RankingDetail(models.Model):
    detail_id = models.BigAutoField(primary_key=True)
    ranking_id = models.IntegerField()
    work_id = models.BigIntegerField()
    stat_date = models.DateField()
    rank = models.IntegerField()
    score = models.DecimalField(max_digits=10, decimal_places=2)
    source_data = models.JSONField()

    class Meta:
        db_table = 'ranking_details'
        unique_together = ('ranking_id', 'work_id', 'stat_date')

