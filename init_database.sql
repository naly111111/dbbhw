-- 创建数据库
CREATE DATABASE IF NOT EXISTS novel_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE novel_platform;

-- 设置客户端连接字符集为UTF-8
SET NAMES utf8mb4;

-- 用户基础表
CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    role TINYINT NOT NULL COMMENT '1=读者，2=作者，3=编辑，9=管理员',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1=正常，0=禁用',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_time DATETIME,
    INDEX idx_username (username),
    INDEX idx_phone (phone),
    INDEX idx_email (email)
);

-- 管理员信息表
CREATE TABLE admins (
    admin_id BIGINT PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    status TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 用户权限控制表
CREATE TABLE user_permissions (
    user_id BIGINT PRIMARY KEY,
    can_publish TINYINT NOT NULL DEFAULT 1,
    can_subscribe TINYINT NOT NULL DEFAULT 1,
    can_recharge TINYINT NOT NULL DEFAULT 1,
    can_comment TINYINT NOT NULL DEFAULT 1,
    can_vote TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 读者信息表
CREATE TABLE readers (
    reader_id BIGINT PRIMARY KEY,
    nickname VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500) DEFAULT '',
    balance DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (reader_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 作者信息表
CREATE TABLE authors (
    author_id BIGINT PRIMARY KEY,
    pen_name VARCHAR(100) NOT NULL UNIQUE,
    intro TEXT,
    identity_status TINYINT NOT NULL DEFAULT 0 COMMENT '0=未认证，1=已认证',
    total_income DECIMAL(12,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 编辑信息表
CREATE TABLE editors (
    editor_id BIGINT PRIMARY KEY,
    real_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    FOREIGN KEY (editor_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 作品类别表
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    parent_id INT,
    sort_num INT NOT NULL DEFAULT 0,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- 作品表
CREATE TABLE works (
    work_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    author_id BIGINT NOT NULL,
    category_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    cover_url VARCHAR(500) DEFAULT '',
    intro TEXT,
    tags TEXT,
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0=草稿，1=连载中，2=完结，3=下架',
    is_signed TINYINT NOT NULL DEFAULT 0 COMMENT '0=未签约，1=已签约',
    read_count BIGINT NOT NULL DEFAULT 0 COMMENT '阅读次数',
    collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
    vote_count INT NOT NULL DEFAULT 0 COMMENT '投票数',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    INDEX idx_author (author_id),
    INDEX idx_category (category_id),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
);

-- 作品管控记录表
CREATE TABLE work_moderations (
    work_id BIGINT PRIMARY KEY,
    is_hidden TINYINT NOT NULL DEFAULT 0,
    chapters_blocked TINYINT NOT NULL DEFAULT 0,
    updates_blocked TINYINT NOT NULL DEFAULT 0,
    subscriptions_blocked TINYINT NOT NULL DEFAULT 0,
    votes_blocked TINYINT NOT NULL DEFAULT 0,
    note TEXT,
    updated_by BIGINT,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 管理员操作日志
CREATE TABLE admin_action_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    target_type TINYINT NOT NULL COMMENT '0=系统,1=用户,2=作品,3=评论,4=章节',
    target_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    detail TEXT,
    extra_data TEXT,
    ip_address VARCHAR(45) DEFAULT '',
    user_agent TEXT,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_admin_time (admin_id, create_time),
    INDEX idx_target (target_type, target_id),
    INDEX idx_action_time (action, create_time)
);

CREATE TABLE user_action_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_type TINYINT,
    target_id BIGINT,
    detail TEXT,
    extra_data TEXT,
    ip_address VARCHAR(45) DEFAULT '',
    user_agent TEXT,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_time (user_id, create_time),
    INDEX idx_action_time (action, create_time),
    INDEX idx_target (target_type, target_id)
);

DELIMITER //
DROP TRIGGER IF EXISTS trg_works_prevent_draft_revert//
CREATE TRIGGER trg_works_prevent_draft_revert
BEFORE UPDATE ON works
FOR EACH ROW
BEGIN
    IF OLD.status IN (1, 2) AND NEW.status = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '已发布作品无法恢复为草稿';
    END IF;
END//
DELIMITER ;

CREATE TABLE chapters (
    chapter_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    work_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content LONGTEXT NOT NULL,
    intro TEXT,
    word_count INT NOT NULL DEFAULT 0,
    is_free TINYINT NOT NULL DEFAULT 1 COMMENT '1=免费，0=付费',
    chapter_order INT NOT NULL,
    status TINYINT NOT NULL DEFAULT 0 COMMENT '0=草稿，1=已发布，2=已下架',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    publish_time DATETIME,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_work_order (work_id, chapter_order),
    INDEX idx_status (status)
);

-- 收藏记录表
CREATE TABLE collections (
    collection_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    collect_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_collection (reader_id, work_id),
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE
);

-- 阅读记录表
CREATE TABLE reading_records (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    chapter_id BIGINT NOT NULL,
    read_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    progress INT NOT NULL DEFAULT 0 COMMENT '阅读进度百分比',
    is_finished TINYINT NOT NULL DEFAULT 0 COMMENT '是否读完',
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id) ON DELETE CASCADE,
    INDEX idx_reader_chapter (reader_id, chapter_id)
);

-- 订阅记录表
CREATE TABLE subscriptions (
    sub_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    chapter_id BIGINT,
    sub_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id) ON DELETE SET NULL
);

-- 投票记录表
CREATE TABLE votes (
    vote_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    vote_type TINYINT NOT NULL COMMENT '1=月票，2=推荐票',
    vote_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    count INT NOT NULL DEFAULT 1,
    message VARCHAR(500) DEFAULT '' COMMENT '投票附带信息',
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    INDEX idx_reader_work (reader_id, work_id),
    INDEX idx_work_time (work_id, vote_time)
);

-- 点券交易记录表
CREATE TABLE point_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    description VARCHAR(255),
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_time (user_id, create_time)
);

-- 搜索记录表
CREATE TABLE search_records (
    search_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    search_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    click_work_id BIGINT,
    search_type TINYINT NOT NULL DEFAULT 1 COMMENT '1=作品搜索，2=作者搜索，3=标签搜索',
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (click_work_id) REFERENCES works(work_id) ON DELETE SET NULL
);

-- 用户推荐反馈表
CREATE TABLE user_recommendation_feedback (
    feedback_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    event_type TINYINT NOT NULL COMMENT '1=点击推荐，2=查看详情，3=收藏，4=阅读，5=订阅，6=投票',
    weight DECIMAL(10,4) NOT NULL DEFAULT 1.0,
    event_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    UNIQUE KEY uniq_user_work_event (user_id, work_id, event_type),
    INDEX idx_feedback_user_time (user_id, event_time),
    INDEX idx_feedback_user_event (user_id, event_type, event_time),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE
);

-- 读者画像表
CREATE TABLE reader_behavior_summary (
    summary_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL UNIQUE,
    favorite_tags TEXT NOT NULL,
    favorite_categories TEXT NOT NULL,
    high_score_works TEXT NOT NULL,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE
);

-- 个性化推荐表
CREATE TABLE personal_recommendations (
    rec_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    rec_rank INT NOT NULL,
    rec_reason VARCHAR(200),
    rec_type TINYINT NOT NULL COMMENT '1=基于收藏，2=基于订阅，3=基于投票，4=基于搜索',
    generate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expire_time DATETIME NOT NULL,
    UNIQUE KEY unique_rec (reader_id, work_id, generate_time),
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE
);

-- 评论表
CREATE TABLE comments (
    comment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reader_id BIGINT NOT NULL,
    work_id BIGINT NOT NULL,
    chapter_id BIGINT,
    content TEXT NOT NULL,
    parent_id BIGINT,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1=正常，0=删除',
    FOREIGN KEY (reader_id) REFERENCES readers(reader_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES comments(comment_id) ON DELETE CASCADE,
    INDEX idx_work (work_id),
    INDEX idx_chapter (chapter_id)
);

-- 签约信息表
CREATE TABLE sign_contracts (
    contract_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    work_id BIGINT NOT NULL UNIQUE,
    author_id BIGINT NOT NULL,
    editor_id BIGINT NOT NULL,
    sign_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    royalty_ratio DECIMAL(5,2) NOT NULL,
    contract_file VARCHAR(500),
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id),
    FOREIGN KEY (editor_id) REFERENCES editors(editor_id)
);

-- 作品审核表
CREATE TABLE work_reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    work_id BIGINT NOT NULL,
    chapter_id BIGINT,
    editor_id BIGINT NOT NULL,
    review_type TINYINT NOT NULL COMMENT '1=上架审核，2=内容审核',
    result TINYINT NOT NULL COMMENT '1=通过，0=驳回',
    comment TEXT,
    review_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id) ON DELETE SET NULL,
    FOREIGN KEY (editor_id) REFERENCES editors(editor_id)
);

-- 榜单表
CREATE TABLE rankings (
    ranking_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_id INT,
    period TINYINT NOT NULL COMMENT '1=日榜，2=周榜，3=月榜，4=总榜',
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    source_type TEXT NOT NULL,
    status TINYINT NOT NULL DEFAULT 1,
    sort_rule VARCHAR(50) NOT NULL DEFAULT 'score DESC',
    display_limit INT NOT NULL DEFAULT 100,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- 榜单详情表
CREATE TABLE ranking_details (
    detail_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ranking_id INT NOT NULL,
    work_id BIGINT NOT NULL,
    stat_date DATE NOT NULL,
    `rank` INT NOT NULL,
    score DECIMAL(10,2) NOT NULL,
    source_data TEXT NOT NULL,
    UNIQUE KEY unique_ranking (ranking_id, work_id, stat_date),
    FOREIGN KEY (ranking_id) REFERENCES rankings(ranking_id) ON DELETE CASCADE,
    FOREIGN KEY (work_id) REFERENCES works(work_id) ON DELETE CASCADE
);

-- 消息表
CREATE TABLE messages (
    message_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sender_id BIGINT,
    recipient_id BIGINT NOT NULL,
    message_type TINYINT NOT NULL,
    content TEXT NOT NULL,
    related_type TINYINT,
    related_id BIGINT,
    is_read TINYINT NOT NULL DEFAULT 0,
    send_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expire_time DATETIME,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (recipient_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_recipient (recipient_id),
    INDEX idx_type (message_type)
);

-- 插入初始数据
INSERT INTO categories (name, parent_id, sort_num) VALUES
('武侠', NULL, 1),
('玄幻', NULL, 2),
('言情', NULL, 3),
('都市', NULL, 4),
('历史', NULL, 5),
('科幻', NULL, 6),
('游戏', NULL, 7),
('悬疑', NULL, 8);

-- 注意：测试用户数据已移至 init_database_testdata.sql
-- 这里不再插入测试数据，避免ID冲突
