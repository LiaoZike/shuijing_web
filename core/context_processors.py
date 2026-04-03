def user_display_name(request):
    """
    Context processor 為所有模板提供處理過的用戶顯示名稱
    顯示完整的姓名（last_name + first_name），如果沒有則使用 email
    """
    if request.user.is_authenticated:
        # 對於中文用戶，正確的順序是姓氏 + 名字
        if request.user.last_name and request.user.first_name:
            display_name = f"{request.user.last_name}{request.user.first_name}"
        elif request.user.first_name:
            display_name = request.user.first_name
        elif request.user.last_name:
            display_name = request.user.last_name
        else:
            # 如果都沒有，使用 email
            display_name = request.user.email
    else:
        display_name = None

    return {
        'user_display_name': display_name
    }