from django.urls import path
from . import views

urlpatterns = [
    # 用户认证
    path('auth/register/', views.user_register, name='user_register'),
    path('auth/login/', views.user_login, name='user_login'),
    path('admin/auth/register/', views.admin_register, name='admin_register'),
    path('admin/auth/login/', views.admin_login, name='admin_login'),
    path('profile/', views.user_profile, name='user_profile'),
    # 管理端接口
    path('admin/users/', views.admin_list_users, name='admin_list_users'),
    path('admin/users/<int:user_id>/permissions/', views.admin_update_user_permissions, name='admin_update_user_permissions'),
    path('admin/works/', views.admin_list_works, name='admin_list_works'),
    path('admin/works/<int:work_id>/moderation/', views.admin_update_work_moderation, name='admin_update_work_moderation'),
    path('admin/chapters/<int:chapter_id>/status/', views.admin_update_chapter_status, name='admin_update_chapter_status'),
    path('admin/comments/', views.admin_list_comments, name='admin_list_comments'),
    path('admin/comments/<int:comment_id>/', views.admin_delete_comment, name='admin_delete_comment'),
    path('admin/action-logs/', views.admin_list_action_logs, name='admin_list_action_logs'),
    path('admin/user-action-logs/', views.admin_list_user_action_logs, name='admin_list_user_action_logs'),

    path('profile/stats/', views.user_profile_stats, name='user_profile_stats'),
    path('profile/contact/', views.update_contact_info, name='update_contact_info'),
    path('profile/password/', views.change_user_password, name='change_user_password'),
    path('profile/recharge/', views.recharge_user_balance, name='recharge_user_balance'),
    path('uploads/avatar/', views.upload_avatar, name='upload_avatar'),
    path('uploads/cover/', views.upload_cover, name='upload_cover'),
    
    # 作品管理
    path('works/', views.get_works, name='get_works'),
    path('works/my-works/', views.get_my_works, name='get_my_works'),
    path('works/create/', views.create_work, name='create_work'),
    path('works/<int:work_id>/', views.get_work_detail, name='get_work_detail'),
    path('works/<int:work_id>/metrics/', views.get_work_metrics, name='get_work_metrics'),
    path('works/<int:work_id>/update/', views.update_work, name='update_work'),
    
    # 章节管理
    path('works/<int:work_id>/chapters/', views.get_chapters, name='get_chapters'),
    path('works/<int:work_id>/chapters/create/', views.create_chapter, name='create_chapter'),
    path('works/<int:work_id>/chapters/<int:chapter_id>/', views.update_chapter, name='update_chapter'),
    path('works/<int:work_id>/chapters/<int:chapter_id>/delete/', views.delete_chapter, name='delete_chapter'),
    path('works/<int:work_id>/chapters/<int:chapter_id>/subscribe/', views.subscribe_chapter, name='subscribe_chapter'),
    
    # 评论与互动
    path('works/<int:work_id>/comments/', views.get_work_comments, name='get_work_comments'),
    path('works/<int:work_id>/comments/create/', views.create_comment, name='create_comment'),
    path('works/<int:work_id>/comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('works/<int:work_id>/comments/<int:comment_id>/', views.update_comment, name='update_comment'),
    path('works/<int:work_id>/comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # 分类管理
    path('categories/', views.get_categories, name='get_categories'),
    
    # 书架
    path('bookshelf/', views.get_bookshelf, name='get_bookshelf'),
    path('bookshelf/add/', views.add_to_bookshelf, name='add_to_bookshelf'),
    path('bookshelf/remove/<int:work_id>/', views.remove_from_bookshelf, name='remove_from_bookshelf'),
    path('subscriptions/records/', views.get_user_subscription_records, name='get_user_subscription_records'),
    path('votes/records/', views.get_user_vote_records, name='get_user_vote_records'),
    path('comments/history/', views.get_comment_history, name='get_comment_history'),
    path('comments/<int:comment_id>/', views.get_comment_thread, name='get_comment_thread'),
    path('comments/<int:comment_id>/delete/', views.delete_user_comment, name='delete_user_comment'),
    
    # 阅读记录
    path('reading/history/', views.get_reading_history, name='get_reading_history'),
    
    # 排行榜
    path('rankings/', views.get_rankings, name='get_rankings'),
    
    # 消息通知
    path('messages/', views.get_messages, name='get_messages'),
    path('messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('messages/mark-all-read/', views.mark_all_messages_read, name='mark_all_messages_read'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    
    # 推荐
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('recommendations/feedback/', views.record_recommendation_feedback, name='record_recommendation_feedback'),

    # 搜索
    path('search/', views.search_works, name='search_works'),
    path('search/history/', views.get_search_history, name='get_search_history'),
    
    # 点券和投票系统
    path('points/', views.get_user_points, name='get_user_points'),
    path('points/purchase/', views.purchase_points, name='purchase_points'),
    path('works/<int:work_id>/vote/', views.vote_work, name='vote_work'),
    path('works/<int:work_id>/votes/', views.get_work_vote_records, name='get_work_vote_records'),
]

