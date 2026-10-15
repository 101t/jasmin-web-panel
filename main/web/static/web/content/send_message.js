(function($){
    var csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var defaultOption = '<option value="">' + escapeHtml(main_trans.defaultCredentials) + '</option>';

    // Fetch users from gateway
    function loadGatewayUsers() {
        $.ajax({
            url: window.location.pathname + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list_users"
            },
            dataType: "json",
            success: function(data){
                var options = defaultOption;
                $.each(data.users || [], function(_, user){
                    // Only show enabled users
                    if (user.status !== 'enabled') return;
                    // The panel only knows the password of users it created; others fall back to
                    // the default credentials, so say so instead of silently sending as someone else.
                    var label = user.uid + ' (' + user.username + ')' + (user.has_password ? '' : ' — ' + main_trans.noPassword);
                    options += '<option value="' + escapeHtml(user.uid) + '"' + (user.has_password ? '' : ' disabled') + '>' +
                        escapeHtml(label) + '</option>';
                });
                $('#user_uid').html(options);
            },
            error: function(jqXHR){
                $('#user_uid').html(defaultOption);
                showAjaxError(jqXHR);
            }
        });
    }

    // Load users on page load
    loadGatewayUsers();

    $("li.nav-item.send-sms-menu").addClass("active");
})(jQuery);
